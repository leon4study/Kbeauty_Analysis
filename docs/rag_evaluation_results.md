# [←](../README.md) RAG 챗봇 평가 결과

`tests/rag_eval/evaluate.py` 로 측정한 K-Beauty 챗봇의 LLM provider 별 비교
결과. 평가 metric 정의는 [`rag_evaluation_framework.md`](rag_evaluation_framework.md).

> 📌 **현재 상태 (2026-05-22)**: LightRAG 변형 (E2) 실제 인덱싱 시도 — **무료
> 한도 (RPM/TPM) 한계 정량 발견**. Groq 4/31 chunks, Gemini 6/31 chunks 부분
> 인덱싱 후 fail. 본격 평가 (60 query × 6 변형) 는 후속 — 해결책 ([§ 무료
> 한도 한계 발견 + 해결책](#무료-한도-한계-발견--해결책)) 적용 후 재시도.

## 무료 한도 한계 발견 + 해결책

### 실측 데이터 (2026-05-22)

LightRAG E2 변형으로 K-Beauty 5브랜드 (100KB) 인덱싱 시도. LightRAG default
concurrency (LLM worker 4) 가 무료 한도 즉시 초과:

| Provider | 무료 한도 | 결과 | 처리 chunk | 실패 원인 |
|---|---|---|---|---|
| Groq Llama 3.3 70B | 12k TPM | 부분 fail | **4 / 31** | TPM 초과 (한 chunk ~6k 토큰 × 4 worker = 24k > 12k) |
| Gemini Flash Lite | 15 RPM | 부분 fail | **6 / 31** | RPM 초과 (4 worker × 빠른 호출 = 즉시 15 RPM 도달) |

→ "*Groq 가 빠르고 Gemini 가 한도 크다*" 가설 검증됐지만, *둘 다 무료
한도만으론 본격 인덱싱 무리*.

### 해결책 4 옵션 (실용성 순)

#### A. **concurrency = 1~2 + LightRAG cache resume** (⭐ 즉시 적용)

- `builder.py` 의 LightRAG 인스턴스에 `llm_model_max_async=2` 설정 (적용됨)
- 더 보수적: `=1` 로 완전 직렬
- LightRAG cache (`llm_response_cache`) 가 chunk-level → 실패 후 재실행 시
  처리된 chunk 자동 skip
- **예상 시간**: 100KB / 31 chunks × 4초 (Gemini 15 RPM) × 3 LLM 호출 ≈ 6 분
- **단점**: 1 회 인덱싱 시간 ~10분 → ~30분 늘어남

#### B. **시간대별 배치 (cron)** (⭐⭐ wrapper script 필요)

```bash
# crontab -e
*/5 * * * * cd /path/to/Kbeauty && python -m src.rag_chatbot.lightrag_variant.index_kbeauty --provider gemini
```

- 5 분마다 인덱싱 시도. cache 살아있으면 *다음 chunk 부터* 처리.
- 31 chunks × 5분 = ~2.5시간 *무인* 완료.
- **단점**: 진행 모니터링 어려움. 실패 알림 별도 필요.

#### C. **Multi-key rotation** (⭐⭐⭐ builder 에 round-robin)

- Gemini key 여러 개 발급 (다른 Google 계정 N개)
- `GEMINI_API_KEYS=key1,key2,key3` 로 받아 round-robin
- 합산 RPM = 15 × N → 즉시 N배 한도
- **단점**: 계정 N개 + 약관 회색지대

#### D. **Hybrid provider pinwheel** (⭐⭐⭐⭐ 큰 변경)

- Groq → Gemini → Cerebras → Together → 회전
- provider 한도 합산 효과
- **단점**: builder.py 의 LLM dispatch 복잡화. 각 provider API key 필요.

### 결정

**A + B 하이브리드** 권장 — 즉시 A 적용 + 시간 여유 있으면 B 추가. C/D 는 *
한도 늘리기* 목적 — 본격 운영 시.

### 똑똑한 도메인 패턴

위 시도에서 얻은 일반 인사이트 (다른 무료 API 활용 프로젝트에도 적용 가능):

1. **무료 한도 = 동시성 적이 제일 비싼 자원** — concurrency 1 직렬화 + retry
   가 가장 안전. 병렬 N worker 는 한도 N배 빠르게 소진.
2. **Resumable cache 가 핵심** — chunk-level cache 없으면 실패마다 처음부터
   재시작 → 영원히 못 끝남. LightRAG 의 `llm_response_cache` 가 좋은 사례.
3. **Provider 별 한도 unit 다름** — Groq=TPM (token), Gemini=RPM (request).
   Wrapper 가 양쪽 다 보호해야.
4. **Tier 1 무료 신청 (Gemini)** — 카드 등록만 하면 RPM 4000 (free tier 의
   270배). 비용 발생 X. 본격 운영 시 권장.

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
