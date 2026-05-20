# tests/rag_eval/ — RAG 챗봇 평가 하네스

K-Beauty 챗봇의 *어떤 LLM provider 가 더 나은가?* 객관적 비교용.

## 파일

| 파일 | 역할 |
|---|---|
| `golden_questions.yaml` | 10 K-Beauty 시나리오 (피부 타입 / 알러지 / 복합 조건) + expected_products + must_not_contain + ground_truth |
| `evaluate.py` | 평가 파이프라인 (챗봇 호출 → metric 계산 → JSON 저장) |
| `results/` | raw 평가 결과 JSON (gitignored 외 .gitkeep 만 포함) |

## 평가 metric

자세히는 [`docs/rag_evaluation_framework.md`](../../docs/rag_evaluation_framework.md).
요약 5 차원:

1. **Retrieval** — Recall@K, MRR (현재 stub, PR-D 에서 구현)
2. **Generation** — RAGAS faithfulness / answer_relevancy (RAGAS optional)
3. **실용** — latency p50/p95, failure rate
4. **도메인 (K-Beauty)** — product_recall, brand_recall, forbidden_violations
5. **일관성** — repeat 5회 응답 variance (PR-D)

## 사용법

### 사전 준비

1. 챗봇 인덱싱 완료 (`src/rag_chatbot/cosmetic_rag_chat/README.md` 참고)
2. `.env` 에 평가할 provider key 등록 (`.env.example` 참고)
3. (선택) RAGAS 설치: `pip install -e .[eval]` — 없어도 도메인 metric 은 동작

### 평가 실행

```bash
# OpenAI 변형 평가
python -m tests.rag_eval.evaluate --provider openai

# Groq 변형
python -m tests.rag_eval.evaluate --provider groq

# Gemini 변형
python -m tests.rag_eval.evaluate --provider gemini

# 출력 경로 명시
python -m tests.rag_eval.evaluate \
    --provider openai \
    --output tests/rag_eval/results/openai_2026_05_20.json
```

### 결과 위치

- raw: `tests/rag_eval/results/<provider>_<date>.json` (gitignored)
- 종합 표: `docs/rag_evaluation_results.md` (PR-D 에서 생성)

## 현재 상태 (PR-D 완료)

- ✓ Golden 10 질문 (5 브랜드 × 피부 타입 × 알러지 × 복합 조건)
- ✓ 도메인 metric (product_recall / brand_recall / forbidden_violations) — rule-based
- ✓ GraphRAG `run_local_search` 실제 호출 (provider 별 settings.yaml 분기)
- ✓ LLM-as-judge metric (faithfulness, answer_relevancy) — judge LLM=Gemini default
- ✓ `--summarize` 모드: 여러 result JSON → markdown 비교 표
- ⏳ 실제 인덱싱 + 평가 실행 (사용자 API key + 인덱싱 필요)
- ⏳ docs/rag_evaluation_results.md 의 placeholder 표 → 실제 수치 갱신

## 골든 질문 추가 시

`golden_questions.yaml` 의 `questions:` 리스트에 같은 schema 로 추가:

```yaml
- id: q11
  category: skin_type  # skin_type / allergy_avoidance / multi_condition
  question: "..."
  expected_products: [...]
  expected_brands: [...]
  must_not_contain: [...]
  ground_truth: |
    ...
```

질문 수 10 → 20+ 으로 늘리면 *통계적 의미* 강해짐. 단 평가 LLM 호출 비용도
비례 증가 — 무료 한도 (Gemini 1.5M TPM/일) 안에서 조절.

## 관련

- [`docs/rag_evaluation_framework.md`](../../docs/rag_evaluation_framework.md)
- [`src/util/llm_provider.py`](../../src/util/llm_provider.py) — 평가에 사용하는 LLM 호출
- [`docs/refactor/15_ollama_graphrag_compatibility.md`](../../docs/refactor/15_ollama_graphrag_compatibility.md) — Ollama 옛 시도 실패 (이 평가의 동기)
