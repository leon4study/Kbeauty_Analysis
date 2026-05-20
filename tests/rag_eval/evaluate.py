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

from util.llm_provider import llm_complete  # noqa: E402

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


def run_chatbot(question: str, provider: str) -> tuple[str, list[str], float]:
    """챗봇에 질문 → (응답, retrieved context, latency_sec) 반환.

    Args:
        question: 사용자 질문.
        provider: "openai" / "groq" / "gemini" / "ollama" 중 하나.
            각각 다른 GraphRAG 인덱스 + LLM 호출 설정 사용.

    Returns:
        (응답 텍스트, context 리스트, 응답 시간 sec). 실패 시
        (에러 메시지, [], 0.0).

    Note:
        실제 챗봇 모듈 (`src/rag_chatbot/cosmetic_rag_chat/main.py`) 의
        ``run_search`` 호출. provider 별 settings.yaml 분기는 PR-D 에서 구현 예정
        — 지금은 stub.
    """
    t0 = time.perf_counter()
    try:
        # TODO (PR-D): provider 별 settings.yaml 분기
        # if provider == "openai":
        #     from rag_chatbot.cosmetic_rag_chat.main import run_search
        #     result = run_search(...)
        # elif provider == "groq":
        #     ...
        #
        # 지금은 stub — 단순 LLM 호출 (retrieval 없음).
        # PR-D 에서 실제 GraphRAG run_search 와 연결.
        from util.llm_provider import llm_complete as _llm
        response = _llm(question, provider=provider if provider in ("groq", "gemini") else None)
        if response is None:
            response = "[ERROR] llm_provider returned None — API key 또는 네트워크 확인"
        contexts: list[str] = []  # GraphRAG 연결 후 실제 retrieved context 채움
        latency = time.perf_counter() - t0
        return response, contexts, latency
    except Exception as e:
        return f"[EXCEPTION] {type(e).__name__}: {e}", [], time.perf_counter() - t0


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


def evaluate_with_ragas(question: str, response: str, contexts: list[str],
                          ground_truth: str, judge_provider: str = "gemini") -> dict[str, float]:
    """RAGAS 사용 — faithfulness / answer_relevancy / context_precision 계산.

    RAGAS 패키지 미설치 시 모든 metric NaN 반환 (graceful fallback).
    judge_provider 는 평가 대상과 다른 provider 사용 권장 (bias 회피).

    Args:
        question: 사용자 질문.
        response: 챗봇 응답.
        contexts: GraphRAG retrieved context 리스트.
        ground_truth: golden yaml 의 정답 텍스트.
        judge_provider: 평가용 LLM provider. default 'gemini'.

    Returns:
        ``{"faithfulness": float, "answer_relevancy": float,
        "context_precision": float}``. RAGAS 미설치 시 모두 NaN.
    """
    try:
        # RAGAS optional — 없으면 NaN 반환.
        import ragas  # noqa: F401
        # TODO (PR-D): 실제 RAGAS evaluate 호출 구현
        # RAGAS 가 LangChain LLM 객체 받으므로 wrapper 필요.
        # 일단 stub 반환.
        return {
            "faithfulness": float("nan"),
            "answer_relevancy": float("nan"),
            "context_precision": float("nan"),
        }
    except ImportError:
        return {
            "faithfulness": float("nan"),
            "answer_relevancy": float("nan"),
            "context_precision": float("nan"),
        }


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

    # 요약 통계
    summary = {
        "provider": provider,
        "judge_provider": judge,
        "timestamp": datetime.now().isoformat(),
        "n_questions": len(results),
        "avg_product_recall": _avg([r["domain"]["product_recall"] for r in results]),
        "avg_brand_recall": _avg([r["domain"]["brand_recall"] for r in results]),
        "total_forbidden_violations": sum(r["domain"]["forbidden_violations"] for r in results),
        "latency_p50": _percentile([r["latency_sec"] for r in results], 50),
        "latency_p95": _percentile([r["latency_sec"] for r in results], 95),
        "failure_count": sum(1 for r in results if r["response"].startswith(("[ERROR]", "[EXCEPTION]"))),
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


def _percentile(xs: list[float], p: int) -> float:
    """간단한 percentile (numpy 의존 회피 — eval 모듈은 가볍게)."""
    if not xs:
        return 0.0
    s = sorted(xs)
    idx = int(len(s) * p / 100)
    return s[min(idx, len(s) - 1)]


def _print_summary(s: dict) -> None:
    print(f"\n📊 요약 ({s['provider']}):")
    print(f"   질문 수:         {s['n_questions']}")
    print(f"   product_recall:  {s['avg_product_recall']:.2%}")
    print(f"   brand_recall:    {s['avg_brand_recall']:.2%}")
    print(f"   금지 키워드:     {s['total_forbidden_violations']} 회")
    print(f"   latency p50:     {s['latency_p50']:.2f}s")
    print(f"   latency p95:     {s['latency_p95']:.2f}s")
    print(f"   실패 수:         {s['failure_count']}/{s['n_questions']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="K-Beauty RAG 챗봇 평가")
    parser.add_argument(
        "--provider",
        choices=["openai", "groq", "gemini", "ollama"],
        required=True,
        help="평가할 LLM provider",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="결과 JSON 저장 경로 (default: results/<provider>_<date>.json)",
    )
    args = parser.parse_args()

    try:
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
