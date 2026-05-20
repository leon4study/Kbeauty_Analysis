# [←](../README.md) RAG 챗봇 평가 프레임워크

K-Beauty GraphRAG 챗봇의 *어떤 LLM provider / RAG 구현이 더 나은가?* 를 객관적으로
비교하기 위한 평가 표준. OpenAI baseline / Groq / Gemini / (선택) LightRAG 등
변형을 동일 기준으로 측정.

## 왜 필요한가

- LLM provider 가 다양해짐 (OpenAI / Groq / Gemini 무료 한도 등)
- "어떤 게 좋다" 는 직관 평가는 portfolio 가치 X
- **재현 가능한 metric** 으로 결정 근거 남기기 → "Groq 가 latency 0.3x, 비용 0, 정확도 95% 유지" 같은 명시적 trade-off 가능

## 5 차원 평가 프레임워크

### 1. Retrieval 품질 (검색 단계)

GraphRAG 가 사용자 질문에 *맞는 entity / 관계* 를 찾아오는가?

| Metric | 정의 | 측정 방법 |
|---|---|---|
| **Recall@K** | 정답 entity 가 top-K 안에 있는 비율 | golden Q&A 의 expected entity vs 실제 retrieve 결과 교집합 |
| **MRR** (Mean Reciprocal Rank) | 정답이 몇 번째에 나오는지 평균 (1/rank) | rank 가 1 이면 1.0, 5 면 0.2 |
| **Precision@K** | top-K 중 진짜 관련 entity 비율 | 사람 평가 (1-5) 또는 LLM-as-judge |

### 2. Generation 품질 (응답 단계)

LLM 이 retrieved context 를 잘 활용해 응답하는가?

| Metric | 정의 | 측정 방법 |
|---|---|---|
| **Faithfulness** | 응답이 retrieved 문서에 근거하는가 (hallucination 측정) | RAGAS (LLM-as-judge, 0-1) |
| **Answer Relevance** | 응답이 질문에 적절한가 | RAGAS (LLM-as-judge, 0-1) |
| **Context Precision** | 사용한 context 중 관련된 비율 | RAGAS |
| **Context Recall** | 정답에 필요한 context 가 빠지지 않았는가 | RAGAS (정답 필요) |

### 3. 실용 metric (운영 관점)

무료 tier 운영 가능성 직접 영향.

| Metric | 정의 | 단위 |
|---|---|---|
| **Latency p50/p95** | query 응답 시간 | ms |
| **Cost per query** | 1 query 당 API 비용 | USD |
| **Failure rate** | rate limit / JSON parse / timeout 비율 | % |
| **Indexing time** | 인덱싱 1회 완료 시간 | min |
| **Indexing cost** | 인덱싱 1회 비용 | USD |

### 4. 도메인 특화 (K-Beauty)

추천 시스템으로서의 가치 — 일반 metric 으로 안 잡힘.

| Metric | 정의 | 측정 방법 |
|---|---|---|
| **피부 타입 매칭** | 사용자 조건 (건성/지성/민감) 에 맞는 제품 추천하는가 | golden Q 의 expected 와 응답 제품 일치율 |
| **알러지 회피** | 제외 조건 (파라벤 알러지 등) 어기지 않는가 | 응답 제품의 성분 검사 |
| **추천 다양성** | 같은 브랜드만 / 같은 제품 타입만 반복 안 하는가 | distinct brand 수, distinct type 수 |

### 5. 일관성 (Reliability)

같은 입력 → 같은 출력?

| Metric | 정의 | 측정 방법 |
|---|---|---|
| **Reproducibility** | 같은 질문 N회 반복 시 응답 variance | 5 회 반복 → semantic similarity (embedding cosine) |

## 도구: RAGAS

RAG 평가 표준 framework — `pip install ragas`.

```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision

result = evaluate(
    dataset=...,  # question, contexts, answer, ground_truth 컬럼
    metrics=[faithfulness, answer_relevancy, context_precision],
    llm=judge_llm,        # 평가용 LLM (Gemini 2.0 Flash 무료로 충분)
    embeddings=judge_emb, # 평가용 embedding
)
```

특징:
- LLM-as-judge 기반 → judge LLM 만 강한 모델이면 평가 자체는 무료 가능
- Faithfulness, Answer Relevance 는 ground truth 없이도 측정 가능
- Context Recall 만 ground truth 필요

## Golden Test Set 설계

`tests/rag_eval/golden_questions.yaml` 에 다음 형식으로:

```yaml
- id: q01
  question: "건성 피부에 맞는 보습 크림 추천해줘"
  expected_products:
    - "COSRX Advanced Snail 92 All In One Cream"
    - "Beauty of Joseon Dynasty Cream"
  expected_brands: ["COSRX", "Beauty of Joseon", "I'm From"]
  must_not_contain: []  # 회피 조건 (이번 케이스는 없음)
  ground_truth: "건성 피부엔 hyaluronic acid, ceramide 함유 제품이 적합..."

- id: q02
  question: "파라벤 알러지 있는데 안전한 클렌저?"
  expected_products: ["COSRX Low pH Good Morning Gel Cleanser"]
  must_not_contain: ["paraben"]  # 응답에 paraben 함유 제품 절대 X
  ground_truth: "..."
```

**최소 10개 질문** (피부 타입 × 알러지 × 제품 타입 조합).

## 평가 워크플로우

```
1. 인덱싱 (3 변형)
   ├─ OpenAI gpt-3.5     (baseline, 기존 결과 재사용)
   ├─ Groq Llama 3.3 70B  (새 인덱싱)
   └─ Gemini 2.0 Flash    (새 인덱싱)

2. 각 변형에 golden 10 질문 던지기
   ├─ 응답 + retrieved context 저장
   ├─ latency 측정
   └─ cost 추적

3. 자동 평가
   ├─ RAGAS (Faithfulness / Answer Relevance / Context Precision)
   ├─ 도메인 매칭 (expected_products / must_not_contain 비교)
   └─ 일관성 (5회 반복 → embedding similarity)

4. 결과 표 → docs/rag_evaluation_results.md
   (system × metric matrix + 해석)

5. 결정: 어느 provider 가 default 로 적합?
```

## 평가 결과 저장 위치

| 단계 | 위치 |
|---|---|
| 평가 프레임워크 (이 문서) | `docs/rag_evaluation_framework.md` |
| golden 질문 세트 | `tests/rag_eval/golden_questions.yaml` |
| 평가 스크립트 | `tests/rag_eval/evaluate.py` |
| raw 결과 (응답 + context) | `tests/rag_eval/results/<provider>_<date>.json` |
| 종합 결과 표 | `docs/rag_evaluation_results.md` |

## 평가 시 주의

1. **Judge LLM bias** — LLM-as-judge 가 자기 family 응답을 더 후하게 평가하는 경향. 가능하면 *제3자 judge* (e.g. 평가 대상이 Groq/OpenAI 면 judge 는 Gemini).
2. **Golden answer 의 주관성** — "추천 제품" 정답이 1개일 수 없음. 합리적 set 으로 정의 + 사람 검토.
3. **샘플 수 한계** — 10개 질문은 통계적으로 약함. trend 만 보고 *결정적 결론 X*. 큰 차이 (latency 10x, faithfulness 0.5 vs 0.9) 만 의미 있음.
4. **재현성** — 모든 변형이 *같은 인덱싱 input* (`examples/graphrag_input/`) 사용. settings.yaml 만 다름.

## 학습 포인트

- **RAG 평가 = retrieval + generation 분리 측정** — 한쪽만 보면 fail 원인 모름
- **LLM-as-judge 가 인간 평가 대용** — 시간/비용 압도적 절감
- **무료 tier 운영 = latency/cost/failure 가 정확도만큼 중요**
- **도메인 metric 은 일반 metric 보다 사용자 가치 직접 반영**

## 관련 docs

- `docs/refactor/15_ollama_graphrag_compatibility.md` — 옛 Ollama 시도 실패 기록 (이 평가의 배경)
- `src/rag_chatbot/cosmetic_rag_chat/README.md` — OpenAI 변형 setup
- `src/rag_chatbot/ollama/README.md` — Ollama 변형 setup
- (예정) `docs/rag_evaluation_results.md` — 실제 평가 결과
- (예정) `tests/rag_eval/` — 골든 질문 + 평가 스크립트
