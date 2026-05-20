# [←](../README.md) RAG 챗봇 평가 결과

`tests/rag_eval/evaluate.py` 로 측정한 K-Beauty 챗봇의 LLM provider 별 비교
결과. 평가 metric 정의는 [`rag_evaluation_framework.md`](rag_evaluation_framework.md).

> ⚠️ **현재 상태**: 인프라 (golden questions + evaluate.py + provider config 템플릿)
> 완비. 실제 인덱싱 + 평가 실행은 사용자 API key 발급 + 인덱싱 후 갱신 예정.

## 평가 환경

- **Golden test set**: `tests/rag_eval/golden_questions.yaml` 10 케이스
- **Judge LLM**: Gemini 2.0 Flash Lite (LLM-as-judge bias 회피용 — 평가 대상 OpenAI/Groq 과 다른 family)
- **인덱싱 input**: `examples/graphrag_input/` (5brand_graphrag_part.txt 또는 brand_50_sample.txt)

## 비교 표 (placeholder — 실행 후 자동 갱신)

```bash
# 세 변형 모두 평가 실행 후
python -m tests.rag_eval.evaluate --summarize \
    tests/rag_eval/results/openai_*.json \
    tests/rag_eval/results/groq_*.json \
    tests/rag_eval/results/gemini_*.json \
    --output docs/rag_evaluation_results_table.md
```

<!-- 아래는 자동 생성 표 들어갈 자리 — 실행 후 직접 갱신 -->

| Metric | OpenAI | Groq | Gemini |
|---|---|---|---|
| product_recall | — | — | — |
| brand_recall | — | — | — |
| forbidden_violations | — | — | — |
| faithfulness (judge) | — | — | — |
| answer_relevancy (judge) | — | — | — |
| latency p50 | — | — | — |
| latency p95 | — | — | — |
| failure_count | — | — | — |
| n_questions | — | — | — |

**해석 가이드**:
- `product_recall` / `brand_recall`: 높을수록 좋음
- `forbidden_violations`: 낮을수록 좋음 (0 이상적)
- `faithfulness`: 응답이 retrieved context 근거 (1.0 = 완전 근거)
- `answer_relevancy`: 응답이 질문에 적절 (1.0 = 직접 답변)
- `latency p95`: 사용자 체감 worst case
- `failure_count`: 인덱싱 미설정 / API 실패

## 비용 비교 (인덱싱 + 챗봇 query)

| 변형 | 인덱싱 1회 | 챗봇 query 1회 | 월간 추정 (1000 query 가정) |
|---|---|---|---|
| OpenAI gpt-3.5-turbo + text-embedding-3-small | ~$5 | ~$0.001 | ~$1 |
| Groq Llama 3.3 70B + OpenAI embedding | ~$5 (임베딩만) | $0 | $0 |
| Gemini 2.0 Flash Lite + text-embedding-004 | $0 (무료 한도) | $0 | $0 |

## 트레이드오프 분석 (틀)

실행 후 다음 패턴으로 작성 예정:

```
**Groq 가 가장 빠르지만 (latency p50 = X 대 OpenAI Y) faithfulness 는 Z만큼 낮음**.
이유: Llama 3.3 70B 가 GraphRAG 의 structured prompt 따라가는 능력 OpenAI 보다
한계 (`docs/refactor/15` 와 일관).

**Gemini 가 비용 0 + faithfulness 유지** — 단 RPM 15 한도라 사용자 동시 접속 시
큐잉 필요.

**결론**: 챗봇 default = Gemini (무료 + 품질 OK), heavy 사용 시 Groq fallback,
인덱싱 정확도 critical 하면 OpenAI 유지.
```

## 재현 방법

```bash
# 1. 의존성
pip install -e .[eval]

# 2. 무료 API key 발급 + .env 등록
#    - Groq: https://console.groq.com (무료 가입)
#    - Gemini: https://aistudio.google.com (무료 가입)

# 3. Provider 별 인덱싱 (3 변형)
#    examples/graphrag_configs/<provider>_settings.yaml 복사 + 인덱싱
#    자세히: examples/graphrag_configs/README.md

# 4. 평가 실행 (각 provider)
python -m tests.rag_eval.evaluate --provider openai
python -m tests.rag_eval.evaluate --provider groq
python -m tests.rag_eval.evaluate --provider gemini

# 5. 종합 표 갱신
python -m tests.rag_eval.evaluate --summarize \
    tests/rag_eval/results/openai_*.json \
    tests/rag_eval/results/groq_*.json \
    tests/rag_eval/results/gemini_*.json \
    --output docs/rag_evaluation_results_table.md

# 6. 이 문서 (rag_evaluation_results.md) 의 표를 results_table.md 내용으로 갱신
```

## 관련

- [`rag_evaluation_framework.md`](rag_evaluation_framework.md) — 평가 metric 정의
- [`refactor/15_ollama_graphrag_compatibility.md`](refactor/15_ollama_graphrag_compatibility.md) — 옛 Ollama 시도 실패
- [`../examples/graphrag_configs/`](../examples/graphrag_configs/) — provider 별 settings.yaml 템플릿
- [`../tests/rag_eval/`](../tests/rag_eval/) — golden questions + evaluate.py
