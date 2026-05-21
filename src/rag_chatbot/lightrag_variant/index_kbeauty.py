"""
File: src/rag_chatbot/lightrag_variant/index_kbeauty.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
무엇 (What) — K-Beauty 5 브랜드 데이터를 LightRAG 인덱스로 insert.
왜 (Why)    — 챗봇 / 평가 사용 전 *1회* 인덱싱. provider 별 working_dir 분리.
어디서 (Where) — 사용자가 CLI 로 직접 실행 (오래 걸림 — Groq 권장).
어떻게 (How)

    # Groq (권장 — 무료 + ~10분)
    python -m src.rag_chatbot.lightrag_variant.index_kbeauty --provider groq

    # Gemini (fallback, 무료, ~30분, rate-limit 주의)
    python -m src.rag_chatbot.lightrag_variant.index_kbeauty --provider gemini

소요 시간 estimate (100KB 입력 기준):
- Groq Llama 3.3 70B: ~10분 (권장)
- Gemini Flash Lite: ~30분 (RPM 한도, fallback)

자세히: docs/lightrag_comparison_design.md (LLM 별 시간 비교)
"""
from __future__ import annotations

import argparse
import asyncio
import sys
import time
from pathlib import Path

# REPO_ROOT 기반 portable import
_HERE = Path(__file__).resolve()
REPO_ROOT = next(p for p in _HERE.parents if (p / ".git").is_dir())
sys.path.insert(0, str(REPO_ROOT / "src"))

# 인덱싱 input — graphrag 변형과 *동일* 파일 사용 (직접 비교 가능).
_INPUT_TXT = REPO_ROOT / "examples" / "graphrag_input" / "5brand_graphrag_part.txt"


async def run_indexing(provider: str) -> int:
    """provider 별 LightRAG 인덱싱 실행 — K-Beauty 5 브랜드 데이터.

    Args:
        provider: ``"groq"`` / ``"gemini"``.

    Returns:
        0=성공, 1=실패.
    """
    from rag_chatbot.lightrag_variant.builder import build_lightrag, insert_text, working_dir_for

    if not _INPUT_TXT.exists():
        print(f"❌ 입력 파일 없음: {_INPUT_TXT}", file=sys.stderr)
        print("  → examples/graphrag_input/README.md 참고")
        return 1

    text = _INPUT_TXT.read_text()
    print(f"\n📚 LightRAG 인덱싱 시작")
    print(f"  provider:    {provider}")
    print(f"  input:       {_INPUT_TXT} ({len(text):,} chars)")
    print(f"  working_dir: {working_dir_for(provider)}")
    print()

    try:
        t_build = time.perf_counter()
        rag = await build_lightrag(provider)
        print(f"✓ build_lightrag ({time.perf_counter() - t_build:.1f}s)")
    except (ImportError, EnvironmentError) as e:
        print(f"❌ build_lightrag 실패: {e}", file=sys.stderr)
        return 1

    print(f"\n⏳ insert 시작 — entity extraction LLM 호출 다수 (수 분 ~ 수 시간)")
    t_insert = time.perf_counter()
    try:
        await insert_text(rag, text)
        elapsed = time.perf_counter() - t_insert
        print(f"\n✓ insert 완료 ({elapsed/60:.1f}분)")
    except Exception as e:
        elapsed = time.perf_counter() - t_insert
        print(f"\n❌ insert 실패 ({elapsed/60:.1f}분): {type(e).__name__}: {e}", file=sys.stderr)
        return 1

    print(f"\n📁 인덱스 위치: {working_dir_for(provider)}")
    print("  → 챗봇 실행: python -m src.rag_chatbot.lightrag_variant.main --provider " + provider)
    print(f"  → 평가 실행: python -m tests.rag_eval.evaluate --provider lightrag-{provider}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="LightRAG K-Beauty 인덱싱 (E2-4)")
    parser.add_argument(
        "--provider",
        choices=["groq", "gemini"],
        required=True,
        help="LLM provider — groq (권장) / gemini (fallback)",
    )
    args = parser.parse_args()
    return asyncio.run(run_indexing(args.provider))


if __name__ == "__main__":
    sys.exit(main())
