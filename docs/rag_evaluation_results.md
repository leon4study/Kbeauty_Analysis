# [←](../README.md) RAG 챗봇 평가 결과

`tests/rag_eval/evaluate.py` 로 측정한 K-Beauty 챗봇의 LLM provider 별 비교
결과. 평가 metric 정의는 [`rag_evaluation_framework.md`](rag_evaluation_framework.md).

> 📌 **현재 상태 (2026-05-23)**: GraphRAG (OpenAI gpt-4o-mini) vs LightRAG
> (Gemini 2.0 Flash Lite) **2-way 비교 실측 완료**. lightrag-groq 는 단일
> request 한도 마주 평가 불가 (Groq 무료 tier 12k TPM 가 LightRAG entity
> extraction prompt ~13k 토큰 처리 못함). 상세는 [§ 무료 한도 한계 발견](#무료-한도-한계-발견--해결책).

## 무료 한도 한계 발견 + 해결책

### 실측 데이터 (2026-05-22 ~ 23)

LightRAG E2 변형으로 K-Beauty 5브랜드 (100KB) 인덱싱 시도. 발견 항목:

| Provider | 한도 종류 | 한도 값 | 결과 | 비고 |
|---|---|---|---|---|
| Groq Llama 3.3 70B (무료) | TPM (분당 토큰) | 12,000 | **single request fail** | LightRAG entity extraction prompt 가 ~13k 토큰 → 단일 request 가 한도 초과 → 어떤 retry/직렬화로도 통과 불가 |
| Gemini Flash Lite (무료) | RPM (분당 요청) | 15 | 6/31 chunks 후 fail | concurrency 16 default 가 즉시 한도 초과 |
| Gemini Flash Lite (**Tier 1**) | RPM | 4,000 | ✅ **31/31 성공 (2.3분)** | 카드 등록 (비용 0) → 270배 한도 |

→ "*Groq 가 빠르고 Gemini 가 한도 크다*" 가설은 일부 사실. 단 **Groq 무료 tier 는
LightRAG 처럼 long-prompt RAG 에는 부적합** (단일 request size 제약). Gemini Tier 1
무료 신청이 무료 LLM RAG 의 *실질 진입점*.

### 해결책 4 옵션 (실측 검증 결과)

#### A. **concurrency = 2 + LightRAG cache resume** (⭐ 부분 효과)

- `builder.py` 에 `llm_model_max_async=2` 설정 (적용됨, [PR #31](https://github.com))
- LightRAG cache (`llm_response_cache`) chunk-level → 실패 후 재실행 시 처리된 chunk 자동 skip
- **실측 결과**: Groq 의 *single request size 한도* 는 해결 불가 (concurrency 무관).
  Gemini 무료 tier 의 *RPM 한도* 는 완화되지만 여전히 부분적.
- **즉 A 만으로 부족** — Gemini Tier 1 등록이 더 큰 효과.

#### B. **시간대별 배치 (cron)** (⭐⭐ Tier 1 후 불필요)

```bash
# crontab -e
*/5 * * * * cd /path/to/Kbeauty && python -m src.rag_chatbot.lightrag_variant.index_kbeauty --provider gemini
```

- 5 분마다 인덱싱 시도. cache 살아있으면 다음 chunk 부터.
- **Tier 1 등록 후엔 불필요** — 한 번에 2.3분 완료.

#### C. **Multi-key rotation** (⭐⭐⭐ 권장 X)

- Gemini key 여러 개 발급 (다른 Google 계정 N개)
- 합산 RPM = 15 × N. **Tier 1 RPM 4000 > 15 × N 보다 훨씬 큼** → 권장 X.

#### D. **Hybrid provider pinwheel** (⭐⭐⭐⭐ Groq 대안 필요 시)

- Groq → Gemini → Cerebras → 회전
- **Groq 의 single request 한도 우회 못 함** — Cerebras/Together 같이 한도 큰 provider 로 대체가 더 효과.

### 결정

**Gemini Tier 1 (무료 카드 등록) + concurrency 2** 가 2026-05-23 실측 검증된 정답.
A/B/C/D 옵션은 **무료 tier 진짜 한계 인 경우만** 의미.

### 똑똑한 도메인 패턴 (다른 무료 API 프로젝트에도)

위 시도에서 얻은 일반 인사이트:

1. **무료 tier 의 *진짜* 한도는 단일 request size** — TPM/RPM 같은 시간 한도는
   직렬화/cache 로 우회 가능하지만, single request 가 한도 초과면 *영구 fail*.
   Groq 12k TPM = single request max = 12k tokens 의미.
2. **Resumable chunk-level cache 가 핵심** — chunk-level cache 없으면 실패마다
   처음부터 재시작 → 영원히 못 끝남. LightRAG `llm_response_cache` 좋은 사례.
3. **Provider 별 한도 unit 다름** — Groq=TPM (token), Gemini=RPM (request).
   Wrapper 가 양쪽 다 보호해야.
4. **Tier 1 무료 신청 (Gemini)** — 카드 등록만 하면 RPM 4000 (free tier 의
   270배). 비용 발생 X (free quota 그대로 + Tier 1 한도 적용). 본격 운영의 *실질
   진입점*.

## 평가 환경

- **Golden test set**: `tests/rag_eval/golden_questions.yaml` 10 케이스 (5 K-Beauty 브랜드)
- **Judge LLM**: Gemini 2.0 Flash Lite (LLM-as-judge bias 회피 — 평가 대상과 다른 family)
- **GraphRAG 인덱스**: `data/model/openaitest_0206/` (2025-02-06 구축, text-embedding-3-small)
- **LightRAG 인덱스**: `data/model/lightrag_gemini/` (2026-05-23 구축, bge-m3 로컬)
- **인덱싱 input**: `examples/graphrag_input/5brand_graphrag_part.txt` (100KB)
- **모델 (평가 시점)**:
  - GraphRAG: gpt-4o-mini, temperature=0, max_tokens=4000
  - LightRAG: gemini-flash-lite-latest, hybrid mode (local + global)

## 비교 표 (2026-05-23 실측)

```bash
# 갱신 명령:
python -m tests.rag_eval.evaluate --summarize \
    tests/rag_eval/results/openai_*.json \
    tests/rag_eval/results/lightrag-gemini_*.json
```

| Metric | LightRAG (gemini) | GraphRAG (openai) | 승자 |
|---|---|---|---|
| `product_recall` | **5.0%** | 3.3% | LightRAG (둘 다 낮음) |
| `brand_recall` | **58.3%** | 26.7% | LightRAG (2.2배) |
| `forbidden_violations` ⚠️ | 11 | **1** | **GraphRAG (안전성 11배)** |
| `faithfulness` (judge) | 0.000 | 0.000 | tie (measurement issue) |
| `answer_relevancy` (judge) | **0.930** | 0.680 | LightRAG |
| `latency p50` | **5.40s** | 6.23s | LightRAG (간소 차) |
| `latency p95` | **6.05s** | 48.82s | LightRAG (cold start 차이) |
| `failure_count` | 0 | 0 | tie |
| `n_questions` | 10 | 10 | — |
| **비용 / 평가 1회** | $0 | ~$0.03 | LightRAG |

_judge LLM: gemini-flash-lite-latest_

**해석 가이드**:
- `product_recall` / `brand_recall`: 높을수록 좋음 (golden expected 매칭율)
- `forbidden_violations`: **낮을수록 좋음** (must_not_contain 위반 — 알러지 회피 등)
- `faithfulness`: 응답이 retrieved context 근거 (1.0 = 완전). 두 변형 모두 0
  → measurement limitation (LightRAG 가 context 안 노출, GraphRAG context 평탄화 손실)
- `answer_relevancy`: 응답이 질문에 적절 (1.0 = 직접 답변)
- `latency p95`: 사용자 체감 worst case (q01 cold start 영향)

## 트레이드오프 분석 — *예상과 다른 결과*

**핵심 발견: 단순 승자 없음. 무료 LightRAG 가 응답 품질 우세, 유료 GraphRAG 가 안전성 우세.**

### LightRAG (Gemini, 무료) 가 우세인 영역

- **brand_recall 2.2배** (58% vs 27%): LightRAG 의 hybrid mode (local + global)
  가 작은 도메인 (5 브랜드) 에 더 잘 맞음
- **answer_relevancy 0.93 vs 0.68**: 응답이 더 풍부 + 질문에 직접
- **latency p95 8배 빠름** (6s vs 49s): GraphRAG cold start 가 community
  summary 로딩으로 ~49s, LightRAG 는 graphml 로딩이 가벼움

### GraphRAG (OpenAI, 유료) 가 우세인 영역

- **forbidden_violations 11배 적음** (1 vs 11): 알러지 회피 등 *반드시 지켜야
  할 제약* 에 11배 우수. 의료/안전 관련 RAG 에서 결정적
- **간결한 응답** (평균 500b vs 800b): community report 기반 답변이 더 정제됨

### 왜 product_recall 이 둘 다 낮은가? (3-5%)

골든 질문의 `expected_products` 가 *합리적 후보군* (e.g. "COSRX Snail 92 Cream"
같은 풀네임) 인데, 두 변형 모두 *카테고리 추천* (e.g. "snail mucin 함유 크림")
으로 응답. 골든 매칭 룰을 *brand + ingredient 동시 매칭* 으로 완화하면 두 변형
모두 점수 크게 오를 듯. 별도 PR 검토.

### 결론 (운영 가이드)

| 사용 시나리오 | 추천 |
|---|---|
| 일반 K-Beauty 추천 챗봇 | **LightRAG (Gemini Tier 1)** — 무료, 응답 풍부 |
| 알러지/안전 critical 추천 | **GraphRAG (OpenAI gpt-4o-mini)** — forbidden 위반 1/11 수준 |
| Hybrid | LightRAG default + must_not_contain rule 별도 필터 추가 |

## 비용 비교 (실측 + 추정)

| 변형 | 인덱싱 1회 | 평가 1회 (10 질문) | 챗봇 1 query | 월 1000 query |
|---|---|---|---|---|
| GraphRAG (OpenAI gpt-4o-mini) | ~$0.06 (인덱스 재구축 시) | ~$0.03 (실측) | ~$0.003 | ~$3 |
| LightRAG (Gemini Tier 1 무료) | $0 (Tier 1 무료 quota) | $0 | $0 | $0 |
| LightRAG (Groq 무료) | **불가** (single request 한도) | — | — | — |

GraphRAG 인덱스는 `openaitest_0206/` 그대로 재사용 가능 (재인덱싱 불요).
LightRAG 인덱스는 2026-05-23 fresh 구축, 2.3 분 소요.

## 알려진 이슈 + 다음 단계

1. **faithfulness 가 둘 다 0** — context 추출 path 가 변형마다 다름:
   - LightRAG: `_run_lightrag` 가 `contexts=[]` 로 return (LightRAG 가 internal
     context 직접 노출 안 함)
   - GraphRAG: `run_local_search` 가 context_data dict 를 list 로 평탄화하지만
     judge 가 평탄화된 텍스트로 faithfulness 검증 어려움
   - → 별도 PR 에서 context 추출 path 통일 필요
2. **product_recall 낮음** — 골든 매칭 룰 완화 검토 (위 §왜)
3. **lightrag-groq 평가 불가** — Groq Dev Tier 등록 (~$0.05/인덱싱) 또는
   Cerebras/Together 추가 시 가능
4. **evaluate.py 종료 시 Queue.get cleanup 에러** — LightRAG worker 가 single
   loop 재사용 시 정상 종료 X. 결과엔 영향 X (JSON 이미 저장됨). 별도 PR 에서 fix

## 재현 방법 (실측 검증된 명령어)

```bash
# 1. 의존성
uv pip install -e .

# 2. API key 발급 + .env 등록
#    - GEMINI_API_KEY: https://aistudio.google.com (무료) + Tier 1 카드 등록 권장
#    - GRAPHRAG_API_KEY: OpenAI key (https://platform.openai.com/api-keys)

# 3. LightRAG 별도 venv (numpy 2.x — main venv 와 충돌)
python -m venv ~/.venvs/kbeauty-lightrag
source ~/.venvs/kbeauty-lightrag/bin/activate
uv pip install -e ".[lightrag]"

# 4. LightRAG 인덱싱 (2.3분, $0)
python -m src.rag_chatbot.lightrag_variant.index_kbeauty --provider gemini

# 5. 평가 실행 (각 provider — main venv 에서 GraphRAG)
deactivate  # → main venv
python -m tests.rag_eval.evaluate --provider openai          # GraphRAG, ~5분, ~$0.03

source ~/.venvs/kbeauty-lightrag/bin/activate
python -m tests.rag_eval.evaluate --provider lightrag-gemini  # LightRAG, ~5분, $0

# 6. 종합 표 갱신
python -m tests.rag_eval.evaluate --summarize \
    tests/rag_eval/results/openai_*.json \
    tests/rag_eval/results/lightrag-gemini_*.json
```

## 관련

- [`rag_evaluation_framework.md`](rag_evaluation_framework.md) — 평가 metric 정의
- [`lightrag_comparison_design.md`](lightrag_comparison_design.md) — LightRAG vs GraphRAG 비교 설계 (E1)
- [`setup_lightrag_env.md`](setup_lightrag_env.md) — LightRAG 별도 venv 가이드
- [`refactor/15_ollama_graphrag_compatibility.md`](refactor/15_ollama_graphrag_compatibility.md) — 옛 Ollama 시도 실패
- [`../examples/graphrag_configs/`](../examples/graphrag_configs/) — provider 별 settings.yaml 템플릿
- [`../tests/rag_eval/`](../tests/rag_eval/) — golden questions + evaluate.py
- [`../tests/rag_eval/results/`](../tests/rag_eval/results/) — 실측 결과 JSON (git tracked baseline)
