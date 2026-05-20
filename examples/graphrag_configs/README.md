# examples/graphrag_configs/ — Provider 별 GraphRAG 설정 템플릿

각 LLM provider 로 인덱싱할 때 사용하는 `settings.yaml` 시작점.

## 파일

| 파일 | provider | 비용 | 한도 |
|---|---|---|---|
| `openai_settings.yaml` | OpenAI gpt-3.5-turbo + text-embedding-3-small | ~$5/인덱싱, $0.001/query | API quota |
| `groq_settings.yaml` | Groq Llama 3.3 70B + OpenAI embedding | $5/인덱싱 (임베딩만), 무료 chat | 1k RPM |
| `gemini_settings.yaml` | Gemini Flash Lite + text-embedding-004 | 0 (인덱싱 + 챗봇) | 15 RPM, 1.5M TPM/일 |

> Groq 는 chat completions 만 제공 — embeddings 는 OpenAI / HuggingFace 별도.
> "완전 무료" 인덱싱은 Gemini 가 유일.

## 사용 흐름

각 provider 별로:

```bash
# 1. 인덱싱 디렉토리 생성 (예: Gemini)
mkdir -p data/model/gemini_t_1/{input,prompts,cache,output}

# 2. 설정 파일 복사
cp examples/graphrag_configs/gemini_settings.yaml \
   data/model/gemini_t_1/settings.yaml

# 3. 인덱싱 입력 데이터 복사
cp examples/graphrag_input/brand_50_sample.txt \
   data/model/gemini_t_1/input/

# 4. GraphRAG prompts 복사 (필수 — entity_extraction, summarize 등)
cp -r src/rag_chatbot/cosmetic_rag_chat/indexing/prompts \
   data/model/gemini_t_1/

# 5. .env 에 API key 등록
echo "GEMINI_API_KEY=AIza..." >> .env

# 6. 인덱싱 실행 (Gemini 의 경우 ~수 십 분, 무료 한도 안)
GRAPHRAG_API_KEY=$GEMINI_API_KEY \
  graphrag index --root ./data/model/gemini_t_1

# 7. 인덱싱 완료 후 settings.yaml 의 data_path 갱신
#    output/<TIMESTAMP>/ 의 실제 timestamp 로 교체
```

## 평가 시 사용

`tests/rag_eval/evaluate.py` 가 provider 별 다른 settings.yaml 자동 로드:

```bash
# Groq 변형 평가
GRAPHRAG_CONFIG_GROQ=data/model/groq_t_1/settings.yaml \
  python -m tests.rag_eval.evaluate --provider groq

# Gemini 변형 평가
GRAPHRAG_CONFIG_GEMINI=data/model/gemini_t_1/settings.yaml \
  python -m tests.rag_eval.evaluate --provider gemini
```

env 미설정 시 default 경로 (`data/model/<provider>_t_1/settings.yaml`) 사용.

## 트러블슈팅

### 임베딩 차원 mismatch

**증상**: 챗봇 query 시 `ValueError: query vector dimension (768) does not match index (1536)`

**원인**: 인덱싱 시 사용한 임베딩 모델과 챗봇 query 시 모델 다름.

**해결**: 같은 settings.yaml 의 `embeddings.llm` 를 인덱싱 + 챗봇에서 동일 사용.

| 임베딩 모델 | 차원 |
|---|---:|
| OpenAI text-embedding-3-small | 1536 |
| OpenAI text-embedding-3-large | 3072 |
| Gemini text-embedding-004 | 768 |
| HuggingFace all-mpnet-base-v2 | 768 |

### Gemini RPM 초과

**증상**: `429 Resource exhausted` 에러.

**원인**: 무료 한도 15 RPM 초과 (4초당 1 req 이상).

**해결**: `parallelization.stagger: 4.0` 또는 더 큰 값으로 조정.

### Groq embeddings 미지원

**증상**: `Embedding endpoint not found`.

**원인**: Groq 가 chat completions 만 제공.

**해결**: `embeddings.llm.api_base` 를 OpenAI 로 변경 (`OPENAI_API_KEY` 별도 등록).

## 관련

- [`../graphrag_input/`](../graphrag_input/) — 인덱싱 입력 데이터 샘플
- [`../../docs/rag_evaluation_framework.md`](../../docs/rag_evaluation_framework.md) — 평가 metric 정의
- [`../../docs/refactor/15_ollama_graphrag_compatibility.md`](../../docs/refactor/15_ollama_graphrag_compatibility.md) — Ollama 시도 실패 (이 fallback 의 배경)
- [`../../src/rag_chatbot/cosmetic_rag_chat/indexing/settings.yaml`](../../src/rag_chatbot/cosmetic_rag_chat/indexing/settings.yaml) — OpenAI 기준 actively-used 설정
