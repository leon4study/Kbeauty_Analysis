"""
File: examples/lightrag_smoke_test/smoke_test.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
무엇인가 (What)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LightRAG + Ollama (gemma2 / bge-m3) 가 *실제로 동작하는지* 검증하는 최소 ping.
5 K-Beauty 브랜드 ~ 5 문장 sample 인덱싱 + 4 query 모드 (naive/local/global/
hybrid) 응답 확인.

왜 있는가 (Why)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"LightRAG 는 Ollama 친화적이라 GraphRAG 대안 가능" *가설* 검증.
LightRAG 공식 README 권장은 ``32B+ 파라미터 모델 + 32KB+ context`` 인데
실제로 gemma2 (9B) 정도로도 의미 있는 entity extraction + query 응답 가능한지
확인 — 결과 따라 Plan E 본격 진행 (E2) vs 폐기 결정.

옛 GraphRAG + Ollama 시도 (``docs/refactor/15``) 가 entity extraction 단계
fail 로 끝났던 경험 → 이번엔 *실제 끝까지 가는지* 작은 sample 로 빠르게.

어디서 쓰이는가 (Where)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
사용자가 *직접* 실행 (Ollama 데몬 + 모델 다운로드 필요). 본 코드는 자동화 X
— 의도적으로 manual smoke. 결과 출력 그대로 새 세션에 공유.

언제 (When)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Plan E (LightRAG 비교) 의 *첫 단계 검증*. E0 통과 → E1 design doc → E2 본격
구현 → E3 평가. 본 ping fail 시 *원인 기록* (어느 단계 / 어떤 에러) 후 E1
에서 대안 검토.

어떻게 (How — 사용자 실행)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1. LightRAG 설치
    pip install lightrag-hku

    # 2. Ollama 모델 다운로드 (LLM + embedding 따로)
    ollama pull gemma2                # LLM (~5GB)
    ollama pull bge-m3                # embedding (~1.2GB, 1024 dim)

    # 3. Ollama 데몬 시작 (이미 떠있으면 skip)
    ollama serve

    # 4. 실행
    cd examples/lightrag_smoke_test
    python smoke_test.py

    # 옵션:
    # python smoke_test.py --llm qwen2.5-coder:7b --embed nomic-embed-text

설계 노트
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- *async API* — LightRAG 가 ``initialize_storages``, ``ainsert``, ``aquery``
  모두 awaitable. ``asyncio.run()`` 으로 wrap.
- *4 query mode 모두 시도* (naive / local / global / hybrid) — naive 만
  embedding 사용 (entity graph 우회), 나머지는 graph 기반. fail 시 어느 모드
  까지 OK 인지 알 수 있음.
- *각 단계 try/except* — 어디서 깨졌는지 명확히. error 단계별 분기.
- *working_dir 격리* — ``./lightrag_storage_smoke/`` 사용. 본 ping 이후 폴더
  삭제 가능.

관련 (Related)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- ``docs/refactor/15_ollama_graphrag_compatibility.md`` — 옛 GraphRAG+Ollama 실패
- ``docs/rag_evaluation_framework.md`` — LightRAG vs GraphRAG 비교 시 사용할 metric
- ``examples/graphrag_input/`` — 같은 도메인 의 더 큰 sample (E2/E3 에서 사용)
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time
from functools import partial
from pathlib import Path

HERE = Path(__file__).resolve().parent
SAMPLE_TXT = HERE / "sample_input.txt"
WORKING_DIR = HERE / "lightrag_storage_smoke"


def print_step(step: str, status: str = "...") -> None:
    """진행 상황 명시 출력 — fail 시 어디서 깨졌는지 stdout 만으로 추적 가능하게."""
    print(f"\n{'='*70}\n[STEP] {step}  ({status})\n{'='*70}")


async def run_smoke_test(llm_model: str, embed_model: str, embed_dim: int) -> int:
    """LightRAG + Ollama 동작 검증. 0=성공, 1=중간 fail.

    각 단계 (import / instantiate / insert / query × 4 mode) 를 try/except 로
    감싸 *어디서 어떻게* 깨졌는지 stdout 에 분명히 남김.

    Args:
        llm_model: Ollama LLM 모델명 (예: gemma2, qwen2.5-coder:7b).
        embed_model: Ollama embedding 모델명 (예: bge-m3, nomic-embed-text).
        embed_dim: 임베딩 차원 (bge-m3=1024, nomic-embed-text=768 등).

    Returns:
        0: 모든 단계 OK. 1: 어느 단계 fail.
    """
    # ─── STEP 1: import ──────────────────────────────────────────────────────
    print_step("import lightrag")
    try:
        from lightrag import LightRAG, QueryParam
        from lightrag.llm.ollama import ollama_model_complete, ollama_embed
        from lightrag.utils import EmbeddingFunc
        print("  ✓ lightrag, lightrag.llm.ollama import OK")
    except ImportError as e:
        print(f"  ❌ ImportError: {e}")
        print("  → `pip install lightrag-hku` 실행됐는지 확인")
        return 1

    # ─── STEP 2: instantiate LightRAG ────────────────────────────────────────
    print_step(f"instantiate LightRAG (llm={llm_model}, embed={embed_model})")
    WORKING_DIR.mkdir(parents=True, exist_ok=True)
    try:
        rag = LightRAG(
            working_dir=str(WORKING_DIR),
            llm_model_func=ollama_model_complete,
            llm_model_name=llm_model,
            summary_max_tokens=8192,
            llm_model_kwargs={
                "host": "http://localhost:11434",
                "options": {"num_ctx": 8192},
                "timeout": 300,
            },
            embedding_func=EmbeddingFunc(
                embedding_dim=embed_dim,
                max_token_size=8192,
                func=partial(
                    ollama_embed,
                    embed_model=embed_model,
                    host="http://localhost:11434",
                ),
            ),
        )
        await rag.initialize_storages()
        print("  ✓ LightRAG instance 생성 + storage 초기화 OK")
    except Exception as e:
        print(f"  ❌ instantiate fail: {type(e).__name__}: {e}")
        print("  → Ollama 데몬 떠있는지 확인 (curl localhost:11434/api/tags)")
        return 1

    # ─── STEP 3: insert sample ──────────────────────────────────────────────
    print_step("insert K-Beauty sample (5 brands, ~5 sentences)")
    sample_text = SAMPLE_TXT.read_text()
    print(f"  입력 텍스트: {len(sample_text)} chars")
    t0 = time.perf_counter()
    try:
        await rag.ainsert(sample_text)
        elapsed = time.perf_counter() - t0
        print(f"  ✓ insert 완료 ({elapsed:.1f}s)")
        print(f"  → working_dir 확인: ls {WORKING_DIR}")
    except Exception as e:
        elapsed = time.perf_counter() - t0
        print(f"  ❌ insert fail ({elapsed:.1f}s): {type(e).__name__}: {e}")
        print("  → entity extraction 단계 실패 가능 — 작은 모델은 LightRAG 구조화 prompt 못 따라감")
        return 1

    # ─── STEP 4: query (4 mode) ──────────────────────────────────────────────
    test_questions = [
        "건성 피부에 맞는 보습 크림 추천해줘",
        "파라벤 알러지 있는데 안전한 클렌저?",
    ]
    modes = ["naive", "local", "global", "hybrid"]

    all_ok = True
    for q in test_questions:
        print_step(f'query: "{q}"')
        for mode in modes:
            t0 = time.perf_counter()
            try:
                response = await rag.aquery(q, param=QueryParam(mode=mode))
                elapsed = time.perf_counter() - t0
                resp_preview = (str(response) or "")[:200].replace("\n", " ")
                print(f"  [{mode:7s}] ({elapsed:5.1f}s) {resp_preview}")
            except Exception as e:
                elapsed = time.perf_counter() - t0
                print(f"  [{mode:7s}] ❌ ({elapsed:5.1f}s) {type(e).__name__}: {str(e)[:150]}")
                all_ok = False

    return 0 if all_ok else 1


def main() -> int:
    p = argparse.ArgumentParser(description="LightRAG + Ollama 동작 검증 (E0 smoke test)")
    p.add_argument("--llm", default="gemma2",
                   help="Ollama LLM 모델 (default gemma2). 더 큰 모델: qwen2.5-coder:7b")
    p.add_argument("--embed", default="bge-m3",
                   help="Ollama embedding 모델 (default bge-m3, 1024 dim). nomic-embed-text=768")
    p.add_argument("--embed-dim", type=int, default=None,
                   help="임베딩 차원. None 이면 모델별 default 추정")
    args = p.parse_args()

    # 임베딩 차원 모델별 default
    if args.embed_dim is None:
        defaults = {
            "bge-m3": 1024,
            "nomic-embed-text": 768,
            "mxbai-embed-large": 1024,
        }
        args.embed_dim = defaults.get(args.embed.split(":")[0], 1024)
        print(f"[info] embedding dim 추정: {args.embed_dim} (모델={args.embed})")

    if not SAMPLE_TXT.exists():
        print(f"❌ sample 파일 없음: {SAMPLE_TXT}", file=sys.stderr)
        return 1

    print(f"\n🧪 LightRAG + Ollama smoke test 시작")
    print(f"   LLM:       {args.llm}")
    print(f"   Embedding: {args.embed} (dim={args.embed_dim})")
    print(f"   Sample:    {SAMPLE_TXT}")
    print(f"   Storage:   {WORKING_DIR}")

    return asyncio.run(run_smoke_test(args.llm, args.embed, args.embed_dim))


if __name__ == "__main__":
    sys.exit(main())
