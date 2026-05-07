# Ollama × Microsoft GraphRAG 호환성 — 왜 OpenAI 로 fallback 했나

K-Beauty 추천 챗봇의 LLM provider 결정 — *비용 0 인 로컬 Ollama* vs *유료 OpenAI cloud*. Ollama 시도했지만 호환성 issue 로 OpenAI 메인 + Ollama 실험 보존 구조로 결정한 흐름 영구 기록.

## 배경 / 의도

K-Beauty 5 브랜드 (COSRX · PURITO · Beauty of Joseon · I'm From · Dr.Jart+) 의 제품·성분·효과 데이터를 Microsoft GraphRAG 로 인덱싱해 *지식 그래프 + 벡터 스토어 (LanceDB)* 만든 뒤, 그 위에서 자연어 추천 챗봇을 운영. 두 단계 모두 LLM 호출 필요:

1. **인덱싱** (1회) — entity extraction, 관계 추출, community summary 등 GraphRAG 의 무거운 LLM 작업
2. **챗봇 query** (지속) — 사용자 자연어 질문에 응답

비용 절감 + 프라이버시 위해 *모든 LLM 호출을 로컬 Ollama 로 처리* 시도했으나, GraphRAG 의 인덱싱 단계에서 호환성 문제 다수 발생. 이 doc 는 *왜 안 됐는지* 와 *어떤 path 로 갈 수 있는지* 영구 기록.

## 시도한 것 (옛 흔적)

`data/model/graphrag_t_2/settings.yaml` 에 Ollama 설정으로 인덱싱 시도:

```yaml
llm:
  api_key: ${GRAPHRAG_API_KEY}   # Ollama 는 임의 값 (dummy) OK
  type: openai_chat              # OpenAI-호환 endpoint 사용
  model: gemma2
  api_base: http://localhost:11434/v1
  model_supports_json: true

embeddings:
  llm:
    type: openai_embedding
    model: nomic-embed-text
    api_base: http://localhost:11434/v1
```

→ `graphrag index --root ./data/model/graphrag_t_2` 실행 시 entity extraction 단계에서 partial fail / lancedb 생성 incomplete.

## 발견된 호환성 문제 3 가지

### 1. Entity extraction 정확도 부족

GraphRAG 의 entity extraction 은 *structured prompt* 로 LLM 에 entity (name, type, description) 를 추출시킨다:

```
# GraphRAG 의 prompt 형태 (간략)
Given a text, identify all entities. Format as:
("entity"<|>NAME<|>TYPE<|>DESCRIPTION)
```

**OpenAI gpt-3.5-turbo / gpt-4** 는 이 prompt 를 잘 따름.

**Ollama 작은 모델** (gemma2 7B, llama3 8B 등) 은:
- Entity 이름 일부 누락 ("salicylic acid" 가 "salicylic" 으로만 추출되는 등)
- Type 태그 형식 깨짐 (예: `INGREDIENT` 대신 `ingredient, 성분` 처럼 일반 텍스트로)
- Description 너무 길거나 비어있음
- Format separator (`<|>`) 무시하고 자연어 응답

→ 결과적으로 entity 데이터가 sparse / inconsistent 해서 그래프 품질 저하. 인덱싱 후반 단계 (community summary, relationship 추출) 에서 cascading fail.

**근본 원인**: 작은 LLM 의 *instruction following* 능력 한계. 70B+ 모델 (Llama 3.3 70B 등) 은 개선될 수 있으나 로컬 vRAM 한계 (40GB+ 필요).

### 2. 임베딩 차원 mismatch

OpenAI 와 Ollama 의 기본 임베딩 차원이 다름:

| 임베딩 모델 | 차원 |
| --- | ---: |
| OpenAI `text-embedding-3-small` | 1536 |
| OpenAI `text-embedding-3-large` | 3072 |
| Ollama `nomic-embed-text` | 768 |
| Ollama `mxbai-embed-large` | 1024 |
| HuggingFace `all-mpnet-base-v2` | 768 |

LanceDB 는 인덱싱 시점의 차원으로 column schema 생성. 챗봇이 *다른 차원의 임베딩 모델로* query 하면 차원 mismatch error:

```
ValueError: query vector dimension (768) does not match index (1536)
```

**필수 제약**: 인덱싱과 챗봇이 동일한 임베딩 모델 사용 (또는 최소 동일 차원).

→ 만약 OpenAI 임베딩으로 인덱싱했으면 챗봇도 OpenAI 임베딩 사용해야 함. *LLM 만 Ollama 로 바꾸기* 도 가능 (HF 임베딩이 LlamaIndex 의 default 일 때).

### 3. JSON mode 안정성

GraphRAG `settings.yaml` 의 `model_supports_json: true` 옵션 — LLM 응답을 valid JSON 으로 강제. OpenAI 는 안정적이나 Ollama 일부 모델은:

- `model_supports_json` 설정해도 가끔 invalid JSON 응답
- Trailing comma, unquoted keys, mixed quotes 등 syntax 오류
- 인덱싱 도중 JSON parse error 로 stop 되거나 partial entity 만 생성

**근본 원인**: Ollama 의 JSON mode 가 OpenAI 대비 덜 enforced. Llama.cpp grammar constraint 사용해야 안정적이나 GraphRAG 가 그 옵션 노출 X.

## 현실적 운영 옵션 3 가지

| 옵션 | 인덱싱 | 챗봇 query (LLM) | 챗봇 임베딩 | 비용 | 동작 보장 |
| --- | --- | --- | --- | --- | --- |
| **A 추천** | OpenAI gpt-3.5-turbo | Ollama (gemma2) | OpenAI text-embedding-3-small (인덱싱과 동일) | ~$5-10 (1회 인덱싱) + 무료 (챗봇) | ✓ |
| B 실험적 | Ollama (gemma2) | Ollama | Ollama (인덱싱과 동일) | 0 | ⚠️ 검증 필요, entity 품질 낮음 |
| C 안전 | OpenAI | OpenAI | OpenAI | ~$5-10 + ~$0.001/query | ✓ |

→ **A 가 가장 현실적 균형점**. 인덱싱 한 번만 OpenAI 비용 발생 + 챗봇 LLM 호출은 Ollama (무료, 무제한). 단 *임베딩은 OpenAI 와 일치* 시켜야 차원 mismatch 안 남.

## 본 프로젝트 결정

- **인덱싱**: OpenAI gpt-3.5-turbo + text-embedding-3-small ([`src/rag_chatbot/cosmetic_rag_chat/indexing/settings.yaml`](../../src/rag_chatbot/cosmetic_rag_chat/indexing/settings.yaml))
- **메인 챗봇**: OpenAI gpt-3.5-turbo ([`src/rag_chatbot/cosmetic_rag_chat/main.py`](../../src/rag_chatbot/cosmetic_rag_chat/main.py)) — 동작 안정 + 응답 품질
- **실험 챗봇**: Ollama gemma2 ([`src/rag_chatbot/ollama/gradio_rag_ch7.py`](../../src/rag_chatbot/ollama/gradio_rag_ch7.py)) — 비용 0 시도, 동작 보장 X
- Portfolio framing: *"Ollama / OpenAI 두 인덱싱 변형 분리 실행해 정확도·비용 trade-off 비교"*

→ Ollama 변형은 *시도했지만 호환성 issue 로 OpenAI 변형이 메인* 의 negative-but-actionable result 로 명시.

## 학습 포인트

1. **Microsoft GraphRAG = OpenAI-first 도구**
   GraphRAG 가 OpenAI API spec 위에서 만들어졌고, 다른 LLM provider 호환은 *"가능하지만 검증 안 됨"* 수준. 공식 docs 도 OpenAI 권장.

2. **임베딩 모델은 인덱싱-챗봇 동일해야**
   차원 mismatch 가 LanceDB + LlamaIndex 환경에서 가장 흔한 fail 포인트. 인덱싱 / 챗봇 / 사용자 업로드 문서 처리 모두 동일 임베딩 모델 사용 필수.

3. **Local LLM 의 entity extraction 성능 한계**
   GraphRAG 의 structured prompt 따르려면 70B+ 모델 필요. 로컬 vRAM 한계 (40GB+) 로 일반 노트북에서 실행 불가. M-시리즈 Mac 의 unified memory 활용해도 64GB+ RAM 필요.

4. **Negative result 도 분석가 가치**
   *시도했지만 안 됐다* 자체가 *기술 한계 인지 능력* 시그널. Portfolio 에 정직히 명시하면 *기술 평가 능력 + 적절한 fallback 선택* 어필.

## 후속 작업 가능 (시도 안 한 것들)

- **더 큰 Ollama 모델 시도** — Llama 3.3 70B / Mixtral 8x22B 같은 모델로 entity extraction 재시도. vRAM 충분한 환경 필요.
- **Custom prompt tuning** — GraphRAG 의 prompt 를 작은 모델 친화적으로 단순화 (entity type 종류 줄임, format 간소화 등)
- **다른 graph RAG 프레임워크** — LightRAG, GraphRAG-LM 같은 대안. 일부는 Ollama 친화적 설계
- **Llama.cpp grammar constraint** — JSON 응답을 grammar-level 에서 강제. GraphRAG 가 노출 안 하는 옵션이라 직접 패치 필요
- **Hybrid embedding** — 인덱싱은 OpenAI, 챗봇은 Ollama LLM + 같은 OpenAI 임베딩 (현재 채택안 — Option A)

## 관련 docs

- [`09_ollama_rag_variants.md`](09_ollama_rag_variants.md) — Ollama 챗봇 ch1 ~ ch8 변종 카탈로그 (이 doc 는 *왜 OpenAI 로 갔는지*, 09 는 *어떤 변종들 있었는지*)
- [`../../src/rag_chatbot/ollama/README.md`](../../src/rag_chatbot/ollama/README.md) — Ollama 변형 사용자 setup
- [`../../src/rag_chatbot/cosmetic_rag_chat/README.md`](../../src/rag_chatbot/cosmetic_rag_chat/README.md) — OpenAI 변형 사용자 setup
- [Microsoft GraphRAG 공식 docs](https://microsoft.github.io/graphrag/) — OpenAI 권장 명시
