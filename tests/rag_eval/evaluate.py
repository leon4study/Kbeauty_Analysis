"""
File: tests/rag_eval/evaluate.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
무엇인가 (What)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
K-Beauty 챗봇의 *다른 LLM provider 변형* (OpenAI / Groq / Gemini / LightRAG 등)
을 ``golden_questions.yaml`` 의 10 케이스로 동일하게 평가하고 비교 표 생성.

왜 있는가 (Why)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*"어떤 provider 가 더 낫나?" 의 객관적 결정 근거* 만들기.
직관 평가 ("Groq 가 더 빠른 것 같다") 는 portfolio 가치 X. 5 차원 metric
(retrieval / generation / 실용 / 도메인 / 일관성) 으로 측정 + 표 생성.

자세한 평가 프레임워크: ``docs/rag_evaluation_framework.md``.

어디서 쓰이는가 (Where)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 사용자가 *인덱싱 완료 후* 직접 실행
- ``python -m tests.rag_eval.evaluate --provider groq --output results/groq_2026_05_20.json``
- 결과 → ``docs/rag_evaluation_results.md`` (PR-D 에서 종합)

언제 실행되는가 (When)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 새 provider 변형 인덱싱 후
- 챗봇 코드 변경 후 regression 검증
- 분기별 정기 (LLM 모델 업데이트 반영)

사용법 (How)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1. 의존성 (RAGAS 옵션) — 도메인 매칭은 RAGAS 없이도 동작
    pip install -e .[eval]

    # 2. 챗봇 인덱싱 완료 상태에서 실행
    python -m tests.rag_eval.evaluate \\
        --provider openai \\
        --output tests/rag_eval/results/openai_2026_05_20.json

    # Groq, Gemini 도 동일
    python -m tests.rag_eval.evaluate --provider groq --output ...
    python -m tests.rag_eval.evaluate --provider gemini --output ...

    # 3. 종합 표 생성 (PR-D 에서 추가 예정)
    python -m tests.rag_eval.evaluate --summarize \\
        results/openai_*.json results/groq_*.json results/gemini_*.json

설계 노트
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- *Chatbot 직접 호출 X* — 챗봇 모듈 (`run_search`) import 해서 사용.
  실제 사용자 플로우와 동일 (retrieval + generation 다 포함).
- *RAGAS 는 optional* — 도메인 매칭 (expected_products / must_not_contain) 은
  pure Python, 의존성 없이 동작. RAGAS 는 faithfulness / answer_relevancy 추가.
- *Judge LLM bias 회피* — 평가 대상이 OpenAI 면 judge 는 Gemini (yaml 의
  ``evaluation.judge_provider``).
- *Raw 결과 보존* — 응답 + retrieved context + latency 까지 JSON 저장.
  RAGAS 재계산 / 새 metric 추가 시 raw 만 있으면 다시 처리 가능.

관련 파일 (Related)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- docs/rag_evaluation_framework.md  ← 평가 metric 정의
- tests/rag_eval/golden_questions.yaml  ← 10 케이스 + expected
- src/util/llm_provider.py  ← judge LLM 호출용
- src/rag_chatbot/cosmetic_rag_chat/main.py  ← 챗봇 query 진입점 (run_search)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

# REPO_ROOT 기준 portable import
REPO_ROOT = next(p for p in [Path.cwd().resolve()] + list(Path.cwd().resolve().parents)
                 if (p / ".git").is_dir())
sys.path.insert(0, str(REPO_ROOT / "src"))

# llm_provider 는 각 함수 안에서 lazy import — 모듈 로드 시 .env 로깅 부작용
# 회피 + summarize 모드 (API 호출 없음) 에선 의존성 없이 동작 가능하게.

GOLDEN_PATH = REPO_ROOT / "tests" / "rag_eval" / "golden_questions.yaml"
RESULTS_DIR = REPO_ROOT / "tests" / "rag_eval" / "results"


def load_golden() -> dict:
    """golden_questions.yaml 로드 + 기본 schema 검증."""
    with open(GOLDEN_PATH) as f:
        data = yaml.safe_load(f)
    if "questions" not in data:
        raise ValueError(f"golden yaml 에 'questions' 키 없음: {GOLDEN_PATH}")
    for q in data["questions"]:
        for key in ("id", "question", "expected_products", "must_not_contain"):
            if key not in q:
                raise ValueError(f"질문 {q.get('id', '?')} 에 '{key}' 누락")
    return data


def _config_path_for(provider: str) -> Path:
    """provider → settings.yaml 경로 매핑.

    ``GRAPHRAG_CONFIG_{PROVIDER}`` env 로 override 가능. 미설정 시 default
    ``data/model/<provider>_t_1/settings.yaml`` 추정 (인덱싱 디렉토리 컨벤션).

    OpenAI 만 기존 ``src/rag_chatbot/cosmetic_rag_chat/indexing/settings.yaml``
    사용 (옛 인덱싱 위치 보존).
    """
    import os
    env_key = f"GRAPHRAG_CONFIG_{provider.upper()}"
    if path := os.getenv(env_key):
        return Path(path)
    if provider == "openai":
        return REPO_ROOT / "src" / "rag_chatbot" / "cosmetic_rag_chat" / "indexing" / "settings.yaml"
    return REPO_ROOT / "data" / "model" / f"{provider}_t_1" / "settings.yaml"


def run_chatbot(question: str, provider: str) -> tuple[str, list[str], float]:
    """챗봇에 질문 → (응답, retrieved context, latency_sec) 반환.

    Provider 별 ``settings.yaml`` 로드 → GraphRAG ``run_local_search`` 호출.
    settings.yaml 안의 ``llm.api_base`` / ``embeddings.llm.api_base`` 가
    provider 마다 다름 (OpenAI / Groq / Gemini).

    Args:
        question: 사용자 질문.
        provider: "openai" / "groq" / "gemini" / "ollama".

    Returns:
        (응답 텍스트, retrieved context 리스트, 응답 시간 sec). 실패 시
        (에러 메시지, [], elapsed).

    Note:
        인덱싱 디렉토리 (``data/model/<provider>_t_1/``) 가 미존재 시 친절한
        에러 + 안내 메시지 반환. 코드 실패가 아니라 *user-actionable* error.
    """
    t0 = time.perf_counter()

    config_path = _config_path_for(provider)
    if not config_path.exists():
        return (
            f"[CONFIG_MISSING] {config_path} 없음. "
            f"인덱싱 안 됐거나 GRAPHRAG_CONFIG_{provider.upper()} env 미설정. "
            f"examples/graphrag_configs/{provider}_settings.yaml 참고.",
            [],
            time.perf_counter() - t0,
        )

    try:
        # GraphRAG 직접 호출 — cosmetic_rag_chat 의 module-level argparse 회피 위해
        # 라이브러리 함수 직접 사용.
        from graphrag.query.cli import run_local_search

        with open(config_path) as f:
            cfg = yaml.safe_load(f) or {}

        # settings.yaml 의 path 들이 상대경로면 REPO_ROOT 기준 절대로 변환.
        def _abs(p: str | None) -> str | None:
            if not p:
                return p
            return str(p) if Path(p).is_absolute() else str(REPO_ROOT / p)

        result = run_local_search(
            _abs(cfg.get("config_path", str(config_path))),
            _abs(cfg.get("data_path")),
            _abs(cfg.get("root_path")),
            int(cfg.get("community_level", 2)),
            cfg.get("response_type", "single paragraph"),
            question,
        )
        # run_local_search 의 반환은 tuple (response, context_data) 가 일반적이나
        # graphrag 버전에 따라 다름. 안전하게 추출.
        if isinstance(result, tuple) and len(result) >= 2:
            response, context_data = result[0], result[1]
        else:
            response, context_data = str(result), {}

        # context_data 는 dict (sources, entities 등). 평가 metric 입력은 단순
        # 텍스트 리스트 → key/value 평탄화.
        contexts: list[str] = []
        if isinstance(context_data, dict):
            for v in context_data.values():
                if isinstance(v, list):
                    contexts.extend(str(x) for x in v)
                else:
                    contexts.append(str(v))

        latency = time.perf_counter() - t0
        return str(response), contexts, latency

    except ImportError as e:
        return (
            f"[IMPORT_ERROR] graphrag 패키지 미설치: {e}. "
            "`pip install -e .` 또는 `pip install graphrag>=0.3.0` 실행.",
            [],
            time.perf_counter() - t0,
        )
    except Exception as e:
        import traceback
        return (
            f"[EXCEPTION] {type(e).__name__}: {str(e)[:200]}\n"
            f"{traceback.format_exc()[:500]}",
            [],
            time.perf_counter() - t0,
        )


def evaluate_domain_match(response: str, expected_products: list[str],
                           expected_brands: list[str],
                           must_not_contain: list[str]) -> dict[str, Any]:
    """도메인 metric 계산 — pure Python, RAGAS 의존성 없음.

    Args:
        response: 챗봇 응답.
        expected_products: 합리적 추천 제품 후보.
        expected_brands: 합리적 추천 브랜드 후보.
        must_not_contain: 절대 포함되면 안 되는 키워드 (성분 등).

    Returns:
        ``{"product_recall": float, "brand_recall": float,
        "forbidden_violations": int}``
        - product_recall: expected 중 응답에 언급된 비율 (0~1).
        - brand_recall: expected_brands 중 응답에 언급된 비율.
        - forbidden_violations: 응답에 must_not_contain 키워드 등장 횟수 (0 이상이면 fail).
    """
    response_lower = response.lower()

    # 제품/브랜드 매칭 — 부분 문자열 검색 (lowercase, normalized whitespace).
    def _normalize(s: str) -> str:
        return re.sub(r"\s+", " ", s.lower().strip())

    response_norm = _normalize(response_lower)

    product_hits = sum(1 for p in expected_products if _normalize(p) in response_norm)
    brand_hits = sum(1 for b in expected_brands if _normalize(b) in response_norm)
    forbidden_hits = sum(response_norm.count(_normalize(f)) for f in must_not_contain)

    return {
        "product_recall": product_hits / len(expected_products) if expected_products else 0.0,
        "brand_recall": brand_hits / len(expected_brands) if expected_brands else 0.0,
        "forbidden_violations": forbidden_hits,
    }


# LLM-as-judge 프롬프트 — 영어 (judge LLM 이 영어 instruction 더 잘 따름).
# 0.0~1.0 단일 숫자만 출력하도록 강제 → parse 안정성.
_FAITHFULNESS_PROMPT = """Rate the FAITHFULNESS of the response on a scale of 0.0 to 1.0.

Question: {question}
Context (retrieved from knowledge base): {context}
Response: {response}

A score of 1.0 means the response is ENTIRELY supported by the context.
A score of 0.0 means the response contains hallucinations not in the context.
A score of 0.5 means partially supported.

Output ONLY the numeric score (e.g., 0.85). No explanation. No extra text."""

_ANSWER_RELEVANCY_PROMPT = """Rate how RELEVANT the response is to the question on a scale of 0.0 to 1.0.

Question: {question}
Response: {response}

1.0 = directly and completely answers the question.
0.5 = partially relevant, missing some aspects.
0.0 = off-topic or irrelevant.

Output ONLY the numeric score (e.g., 0.75). No explanation. No extra text."""


def _parse_judge_score(raw: str | None) -> float:
    """judge LLM 응답 (e.g. "0.85" 또는 "Score: 0.85") 에서 첫 숫자 추출.

    LLM 이 prompt 잘 따르면 "0.85" 같이 단일 숫자, 가끔 "Score: 0.85" /
    "0.85\\n..." 등 자유 형식. 정규식으로 0.0~1.0 범위 첫 float 매칭.

    Args:
        raw: judge LLM 응답 (None 가능).

    Returns:
        파싱된 점수 (0.0~1.0) 또는 NaN (실패 시).
    """
    if not raw:
        return float("nan")
    m = re.search(r"(\d?\.\d+|\d)", raw)
    if not m:
        return float("nan")
    try:
        score = float(m.group(1))
        # 범위 강제 — judge 가 1.5 같은 거 내놓으면 1.0 으로 clip.
        return max(0.0, min(1.0, score))
    except ValueError:
        return float("nan")


def evaluate_with_judge(question: str, response: str, contexts: list[str],
                         ground_truth: str, judge_provider: str = "gemini") -> dict[str, float]:
    """LLM-as-judge 로 faithfulness / answer_relevancy 평가.

    RAGAS 라이브러리 없이 ``llm_provider.llm_complete`` 직접 사용 (judge 도
    무료 한도 안에서). RAGAS 의 핵심 metric 2 개 (faithfulness + answer_relevancy)
    만 구현 — context_precision 은 더 복잡 (claim 단위 추출 필요), 일단 skip.

    Args:
        question: 사용자 질문.
        response: 챗봇 응답.
        contexts: GraphRAG retrieved context 리스트.
        ground_truth: golden yaml 정답 텍스트 (현재 미사용, 추후 contextrecall 용).
        judge_provider: 평가용 LLM ('gemini' / 'groq'). 평가 대상과 다른 provider
            권장 (bias 회피). default 'gemini'.

    Returns:
        ``{"faithfulness": 0.0~1.0, "answer_relevancy": 0.0~1.0,
        "context_precision": NaN (미구현)}``.
        모든 score 는 평가 호출 실패 시 NaN.
    """
    # 응답 자체가 에러면 평가 skip — judge 호출 비용 절약 + 의미 없는 score 회피.
    if response.startswith(("[ERROR]", "[EXCEPTION]", "[CONFIG_MISSING]", "[IMPORT_ERROR]")):
        return {
            "faithfulness": float("nan"),
            "answer_relevancy": float("nan"),
            "context_precision": float("nan"),
        }

    from util.llm_provider import llm_complete as _llm

    # context 가 너무 길면 judge 토큰 한도 초과 — 앞 3000자만 사용.
    ctx_str = "\n---\n".join(contexts)[:3000] if contexts else "(no context)"

    # Faithfulness: response 가 context 근거인가.
    faith_prompt = _FAITHFULNESS_PROMPT.format(
        question=question, context=ctx_str, response=response,
    )
    faith_raw = _llm(faith_prompt, provider=judge_provider,
                     max_tokens=10, temperature=0.0, timeout=30.0)
    faithfulness = _parse_judge_score(faith_raw)

    # Answer relevancy: response 가 question 에 적절한가 (context 무관).
    rel_prompt = _ANSWER_RELEVANCY_PROMPT.format(
        question=question, response=response,
    )
    rel_raw = _llm(rel_prompt, provider=judge_provider,
                   max_tokens=10, temperature=0.0, timeout=30.0)
    answer_relevancy = _parse_judge_score(rel_raw)

    return {
        "faithfulness": faithfulness,
        "answer_relevancy": answer_relevancy,
        # context_precision 은 claim 단위 분해 필요 → 추후 추가. 일단 NaN.
        "context_precision": float("nan"),
    }


# 옛 이름 유지 (BC). 새 이름 evaluate_with_judge 권장.
evaluate_with_ragas = evaluate_with_judge


def run_evaluation(provider: str, output_path: Path | None = None) -> dict:
    """전체 평가 파이프라인 — golden 10 질문 → metric 계산 → JSON 저장.

    Args:
        provider: 평가할 LLM provider ('openai' / 'groq' / 'gemini' / 'ollama').
        output_path: 결과 저장 경로. None 이면 ``results/<provider>_<date>.json``.

    Returns:
        결과 dict (results 리스트 + 요약 통계).
    """
    golden = load_golden()
    judge = golden.get("evaluation", {}).get("judge_provider", "gemini")

    print(f"\n🧪 평가 시작 — provider={provider}, judge={judge}")
    print(f"   질문 수: {len(golden['questions'])}\n")

    results = []
    for q in golden["questions"]:
        print(f"  [{q['id']}] {q['question'][:50]}...")
        response, contexts, latency = run_chatbot(q["question"], provider)

        domain = evaluate_domain_match(
            response, q["expected_products"],
            q.get("expected_brands", []),
            q.get("must_not_contain", []),
        )
        ragas = evaluate_with_ragas(
            q["question"], response, contexts,
            q.get("ground_truth", ""), judge_provider=judge,
        )

        results.append({
            "id": q["id"],
            "category": q.get("category", "uncategorized"),
            "question": q["question"],
            "response": response,
            "contexts": contexts,
            "latency_sec": round(latency, 3),
            "domain": domain,
            "ragas": ragas,
        })

    # 요약 통계 — 도메인 + 실용 + LLM-as-judge metric 모두 평균.
    # NaN 값은 _avg_finite 가 제외 후 평균 (judge LLM 실패 row 영향 X).
    summary = {
        "provider": provider,
        "judge_provider": judge,
        "timestamp": datetime.now().isoformat(),
        "n_questions": len(results),
        # 도메인 (pure Python, NaN 없음)
        "avg_product_recall": _avg([r["domain"]["product_recall"] for r in results]),
        "avg_brand_recall": _avg([r["domain"]["brand_recall"] for r in results]),
        "total_forbidden_violations": sum(r["domain"]["forbidden_violations"] for r in results),
        # LLM-as-judge (judge 호출 실패 시 NaN — 평균에서 제외)
        "avg_faithfulness": _avg_finite([r["ragas"]["faithfulness"] for r in results]),
        "avg_answer_relevancy": _avg_finite([r["ragas"]["answer_relevancy"] for r in results]),
        # 실용
        "latency_p50": _percentile([r["latency_sec"] for r in results], 50),
        "latency_p95": _percentile([r["latency_sec"] for r in results], 95),
        "failure_count": sum(
            1 for r in results
            if r["response"].startswith(("[ERROR]", "[EXCEPTION]", "[CONFIG_MISSING]", "[IMPORT_ERROR]"))
        ),
    }

    output = {"summary": summary, "results": results}

    if output_path is None:
        date_str = datetime.now().strftime("%Y_%m_%d_%H%M%S")
        output_path = RESULTS_DIR / f"{provider}_{date_str}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))

    print(f"\n✓ 결과 저장: {output_path}")
    _print_summary(summary)
    return output


def _avg(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _avg_finite(xs: list[float]) -> float:
    """NaN 제외 평균 — LLM-as-judge 실패 row 가 통계 오염 안 시키게."""
    finite = [x for x in xs if x == x]  # NaN != NaN trick
    return sum(finite) / len(finite) if finite else float("nan")


def _percentile(xs: list[float], p: int) -> float:
    """간단한 percentile (numpy 의존 회피 — eval 모듈은 가볍게)."""
    if not xs:
        return 0.0
    s = sorted(xs)
    idx = int(len(s) * p / 100)
    return s[min(idx, len(s) - 1)]


def _fmt(v: float, kind: str = "pct") -> str:
    """NaN-safe 포맷터.

    Args:
        v: 표시할 숫자.
        kind: 'pct' (퍼센트) / 'num' (소수점 2자리) / 'sec' (시간).
    """
    if v != v:  # NaN
        return "—"
    if kind == "pct":
        return f"{v:.1%}"
    if kind == "sec":
        return f"{v:.2f}s"
    return f"{v:.3f}"


def _print_summary(s: dict) -> None:
    print(f"\n📊 요약 ({s['provider']}, judge={s['judge_provider']}):")
    print(f"   질문 수:           {s['n_questions']}")
    print(f"   ── 도메인 (rule-based) ──")
    print(f"   product_recall:    {_fmt(s['avg_product_recall'])}")
    print(f"   brand_recall:      {_fmt(s['avg_brand_recall'])}")
    print(f"   금지 키워드 위반:  {s['total_forbidden_violations']} 회")
    print(f"   ── LLM-as-judge ──")
    print(f"   faithfulness:      {_fmt(s['avg_faithfulness'], 'num')}")
    print(f"   answer_relevancy:  {_fmt(s['avg_answer_relevancy'], 'num')}")
    print(f"   ── 실용 ──")
    print(f"   latency p50:       {_fmt(s['latency_p50'], 'sec')}")
    print(f"   latency p95:       {_fmt(s['latency_p95'], 'sec')}")
    print(f"   실패 수:           {s['failure_count']}/{s['n_questions']}")


def summarize_to_markdown(result_paths: list[Path]) -> str:
    """여러 provider 의 result JSON 들을 읽어 비교 markdown 표 생성.

    Args:
        result_paths: ``run_evaluation`` 가 저장한 JSON 경로 리스트.
            각 파일이 한 provider 의 평가 결과.

    Returns:
        markdown 문자열 — provider × metric 표 + 해석 가이드.

    Output 형식 (예시):
        | Metric              | OpenAI | Groq   | Gemini |
        |---------------------|--------|--------|--------|
        | product_recall      | 70.0%  | 50.0%  | 60.0%  |
        | brand_recall        | 80.0%  | 90.0%  | 80.0%  |
        | forbidden_violations| 0      | 2      | 0      |
        | faithfulness        | 0.85   | 0.72   | 0.78   |
        | answer_relevancy    | 0.92   | 0.88   | 0.85   |
        | latency p50         | 1.20s  | 0.45s  | 0.80s  |
        | latency p95         | 2.10s  | 0.90s  | 1.40s  |
        | failure_count       | 0      | 1      | 0      |
    """
    summaries = []
    for p in result_paths:
        with open(p) as f:
            data = json.load(f)
        summaries.append(data["summary"])

    if not summaries:
        return "(no results)\n"

    # 헤더
    providers = [s["provider"] for s in summaries]
    lines = [
        "| Metric | " + " | ".join(providers) + " |",
        "|" + "---|" * (len(providers) + 1),
    ]

    # metric 별 행 — (key, format kind, label) 매핑.
    rows = [
        ("avg_product_recall",    "pct", "product_recall"),
        ("avg_brand_recall",      "pct", "brand_recall"),
        ("total_forbidden_violations", "int", "forbidden_violations"),
        ("avg_faithfulness",      "num", "faithfulness (judge)"),
        ("avg_answer_relevancy",  "num", "answer_relevancy (judge)"),
        ("latency_p50",           "sec", "latency p50"),
        ("latency_p95",           "sec", "latency p95"),
        ("failure_count",         "int", "failure_count"),
        ("n_questions",           "int", "n_questions"),
    ]

    for key, kind, label in rows:
        cells = []
        for s in summaries:
            v = s.get(key)
            if v is None:
                cells.append("—")
            elif kind == "int":
                cells.append(str(int(v)))
            else:
                cells.append(_fmt(v, kind))
        lines.append(f"| {label} | " + " | ".join(cells) + " |")

    # 해석 가이드 추가
    lines.append("")
    lines.append("**해석**:")
    lines.append("- `product_recall` / `brand_recall`: 높을수록 좋음 (golden expected 매칭율)")
    lines.append("- `forbidden_violations`: 낮을수록 좋음 (0 이 이상적, 알러지 회피 등)")
    lines.append("- `faithfulness`: 응답이 retrieved context 에 근거하는지 (1.0 = 완전 근거)")
    lines.append("- `answer_relevancy`: 응답이 질문에 적절한지 (1.0 = 직접 답변)")
    lines.append("- `latency p95`: 95%-tile 응답시간 (사용자 체감 worst case)")
    lines.append("- `failure_count`: 인덱싱 미설정 / API 실패 등으로 응답 못 한 질문 수")
    lines.append("")
    lines.append(f"_judge LLM: {summaries[0].get('judge_provider', '?')}_")
    lines.append(f"_평가 일시: {summaries[0].get('timestamp', '?')}_")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="K-Beauty RAG 챗봇 평가",
        epilog=(
            "예시:\n"
            "  # 단일 provider 평가\n"
            "  python -m tests.rag_eval.evaluate --provider gemini\n\n"
            "  # 여러 provider 결과 종합 → markdown 표\n"
            "  python -m tests.rag_eval.evaluate --summarize \\\n"
            "      tests/rag_eval/results/openai_*.json \\\n"
            "      tests/rag_eval/results/groq_*.json \\\n"
            "      tests/rag_eval/results/gemini_*.json\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # 두 모드 — 평가 실행 vs 결과 종합. 상호 배타적.
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--provider",
        choices=["openai", "groq", "gemini", "ollama"],
        help="단일 provider 평가 실행",
    )
    mode.add_argument(
        "--summarize",
        nargs="+",
        type=Path,
        metavar="RESULT_JSON",
        help="여러 result JSON → 종합 markdown 표 stdout 출력",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "--provider 모드: 결과 JSON 저장 경로 "
            "(default: results/<provider>_<date>.json). "
            "--summarize 모드: markdown 표 저장 경로 (default: stdout)"
        ),
    )
    args = parser.parse_args()

    try:
        if args.summarize:
            # 종합 모드 — JSON 파일들 읽어서 markdown 표.
            md = summarize_to_markdown(args.summarize)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(md)
                print(f"✓ markdown 표 저장: {args.output}")
            else:
                print(md)
            return 0

        # 평가 모드
        run_evaluation(args.provider, args.output)
        return 0
    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ {type(e).__name__}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
