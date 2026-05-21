# [←](../README.md) LightRAG vs GraphRAG 비교 — 시도 기록

GraphRAG 대안으로 LightRAG 를 *시도해본* 작업의 설계 + E0 검증 결과 정리.
메인 챗봇은 여전히 GraphRAG (`cosmetic_rag_chat`) — 본 LightRAG 변형은 *비교
실험* 위치. 평가 결과 보고 메인 채택 여부 결정 예정.

## E0 결과 (이 design 의 근거)

`examples/lightrag_smoke_test/smoke_test.py` 실행 결과 (2026-05-21):

```
LLM:       gemma2 (Ollama 로컬, 9B)
Embedding: bge-m3 (Ollama 로컬, 1024 dim)
Sample:    K-Beauty 5 브랜드 ~5 문장 (1019 chars)
```

| 단계 | 시간 | 결과 |
|---|---|---|
| Import | 즉시 | ✓ |
| Instantiate | 즉시 | ✓ |
| **Insert (entity extraction)** | **250s** | ✓ **15 entities + 9 relations 추출** |
| Query naive | 29s | ✓ "COSRX Snail 92, Beauty of Joseon Dynasty Cream..." |
| Query local | 54s | ✓ "Beauty of Joseon Dynasty Cream, I'm From Mugwort..." |
| Query global | 80s | ✓ "Beauty of Joseon Dynasty Cream, I'm From Mugwort..." |
| Query hybrid | 49s | ✓ "Dr.Jart+ Ceramidin Cream, Beauty of Joseon Dynasty..." |

**핵심 발견**: 옛 GraphRAG + Ollama 가 *entity extraction 단계 fail* 였던 곳에서
LightRAG + gemma2 는 *15 entities 정상 추출*. "LightRAG = 작은 LLM 친화적" 가설
입증.

## 1. LightRAG vs GraphRAG 아키텍처 비교

| 항목 | Microsoft GraphRAG | HKUDS LightRAG |
|---|---|---|
| **목적** | enterprise-grade knowledge graph + community summary | lightweight RAG with entity graph |
| **Entity extraction prompt** | 매우 strict (`<\|>` separator + 다단계 gleaning) | 단순 (자연어 + 단일 패스) |
| **권장 LLM 크기** | GPT-3.5+ / Llama 70B+ | 32B+ (공식) — 실측은 9B 도 가능 |
| **인덱싱 단계** | Documents → Text Units → Entities → Relations → Communities → Summaries (5+) | Documents → Chunks → Entities → Relations (3) |
| **Storage** | Parquet 파일 + LanceDB | JSON + nano-vectordb (in-process) |
| **Query modes** | local / global / drift | naive / local / global / hybrid |
| **Embedding** | OpenAI / HuggingFace | Ollama / OpenAI / HuggingFace 어디든 |
| **API style** | sync CLI + Python (run_local_search 등) | async Python (ainsert / aquery) |
| **공식 docs** | OpenAI-first | provider-agnostic |
| **Repo** | microsoft/graphrag (Microsoft 공식) | HKUDS/LightRAG (학술팀 오픈소스) |

### 아키텍처 의미

- GraphRAG 의 "community summary" 단계는 LightRAG 에 없음 — *대규모 그래프 요약*
  필요할 때 GraphRAG 유리.
- LightRAG 의 4 query mode 중 `naive` 는 *entity graph 우회* (단순 RAG) — graph
  품질 낮아도 응답 가능. `hybrid` 는 entity + chunk 결합.
- LightRAG 의 async 패턴 — 우리 챗봇 (Gradio sync) 과 묶을 때 ``asyncio.run``
  wrap 필요.

## 2. 평가 framework 적용 방법

`docs/rag_evaluation_framework.md` 의 5 차원 metric 을 LightRAG 변형에도 동일
적용:

### 추가 변형

기존 평가 대상 (PR-D 까지 wired):
- OpenAI (gpt-3.5-turbo + text-embedding-3-small)
- Groq (Llama 3.3 70B + 외부 임베딩)
- Gemini (Flash Lite + text-embedding-004)

**신규 추가**: LightRAG × {Ollama, Groq, Gemini} 3 변형.
→ 총 6 변형 비교 (GraphRAG 3 + LightRAG 3) 가능.

### evaluate.py 통합

```python
# tests/rag_eval/evaluate.py 의 run_chatbot() 분기 확장:
def run_chatbot(question, provider):
    if provider.startswith("lightrag_"):
        # lightrag_ollama / lightrag_groq / lightrag_gemini
        return _run_lightrag(question, provider)
    else:
        # 기존 graphrag 경로
        return _run_graphrag(question, provider)
```

LightRAG 변형도 동일 golden 10 질문 + 같은 metric → 직접 비교.

## 3. K-Beauty 본격 데이터 인덱싱 계획

E0 는 1KB sample. 본격 비교는 `examples/graphrag_input/5brand_graphrag_part.txt`
(100KB) 사용 — GraphRAG 변형과 *같은 input*.

### LLM 선택 별 인덱싱 시간 / 비용 estimate

E0 의 1019 chars → 250s 기준 비례 추정 + LLM 성능 보정:

| LLM | 추정 시간 | 비용 | 비고 |
|---|---|---|---|
| Ollama gemma2 (CPU) | **~7시간** (rough) | 0 | 100KB / 1KB × 250s = ~7시간. M-series GPU 시 단축 가능 |
| Ollama qwen2.5-coder:7b | ~5시간 | 0 | gemma2 보다 빠름 (4-bit 양자화 기준) |
| Groq Llama 3.3 70B | ~10분 | 0 | API 빠름, 무료 한도 (1k RPM) 안 |
| Gemini Flash Lite | ~30분 | 0 | 15 RPM 한도 → stagger 4s 필요 |
| OpenAI gpt-3.5-turbo | ~10분 | ~$3 | 가장 검증된 정확도 |

**권장**: Groq Llama 3.3 70B — 무료 + 빠름 + 정확도 충분 추정.
Fallback: Gemini (Groq rate-limit 시).

### LightRAG 의 LLM 분리 가능성

LightRAG 의 핵심: ``llm_model_func`` 와 ``embedding_func`` 가 *plug-and-play*.
즉 *같은 LightRAG 인덱스* 에 LLM 만 갈아끼울 수 있음 (인덱싱은 한 번, query 는
여러 LLM):

```python
# 인덱싱: Groq (빠른 entity extraction)
rag = LightRAG(llm_model_func=groq_complete, ...)
await rag.ainsert(text)

# Query: 다른 LLM 으로 시도 (인덱스 재사용)
rag2 = LightRAG(llm_model_func=gemini_complete, working_dir=same_dir, ...)
result = await rag2.aquery(q)
```

→ *인덱싱 1회로 N LLM query 비교* 가능. 우리 ``src/util/llm_provider.py`` 와 직접
호환.

## 4. 의존성 충돌 해결

E0 설치 시 발견된 충돌:

```
graphrag 0.3.0   requires numpy<2.0.0  but lightrag-hku 가져온 numpy 2.2.6
gradio 5.14.0    requires aiofiles<24  but lightrag 의존 aiofiles 24.1.0
graspologic 3.4  requires numpy<2.0    (graphrag 의 transitive)
llama-index-core requires nltk>3.8.1   but 3.8.1 (gradio 의존?)
```

### 옵션 A — 별도 venv (권장)

```bash
# 새 venv (graphrag 와 격리)
python3 -m venv ~/.venvs/lightrag
source ~/.venvs/lightrag/bin/activate
pip install -e ".[lightrag]"   # pyproject.toml 에 [lightrag] extra 추가
```

장점: 두 변형 동시 운영 가능.
단점: venv 2 개 관리.

### 옵션 B — pyproject extras 분리

```toml
[project.optional-dependencies]
graphrag-chatbot = [
    "graphrag>=0.3.0",
    "numpy<2.0",
    ...
]
lightrag-chatbot = [
    "lightrag-hku>=1.4",
    "numpy>=2.0",
    ...
]
# all 에서 충돌하는 것 제거
```

장점: 하나의 pyproject.
단점: ``pip install -e .[all]`` 실패 (numpy 충돌).

### 옵션 C — graphrag 폐기

LightRAG 가 GraphRAG 보다 모든 면에서 우수하면 graphrag 의존성 자체 제거.
*비교 결과 후* 결정 가능.

**1차 진행**: 옵션 A (별도 venv) — 비교 끝나기 전 graphrag 도 보존.

## 5. evaluate.py 통합 방법

### 5.1 provider naming

```
provider=openai      → GraphRAG + OpenAI
provider=groq        → GraphRAG + Groq (PR-D)
provider=gemini      → GraphRAG + Gemini (PR-D)
provider=lightrag-ollama  → LightRAG + Ollama gemma2 (신규)
provider=lightrag-groq    → LightRAG + Groq (신규)
provider=lightrag-gemini  → LightRAG + Gemini (신규)
```

### 5.2 run_chatbot() 분기

```python
def run_chatbot(question, provider):
    if provider.startswith("lightrag-"):
        backend = provider.replace("lightrag-", "")  # ollama / groq / gemini
        return _run_lightrag(question, backend)
    return _run_graphrag(question, provider)  # 기존
```

### 5.3 LightRAG instance 캐싱

매 query 마다 LightRAG 인스턴스 새로 만들면 storage 다시 로드 → 느림. 모듈
level singleton 또는 ``lru_cache``:

```python
@functools.lru_cache(maxsize=4)
def _get_lightrag(backend: str) -> LightRAG:
    # backend 별 settings.yaml 로드 후 LightRAG 인스턴스 반환
    ...
```

## 6. LightRAG 변형 챗봇 위치

### 옵션 A — 새 디렉토리

```
src/rag_chatbot/
  cosmetic_rag_chat/    # 기존 OpenAI GraphRAG
  ollama/               # 기존 Ollama GraphRAG (실험)
  lightrag_variant/     # 신규 LightRAG (this design)
  ├── main.py           # Gradio entry point
  ├── indexing/         # LightRAG storage
  └── README.md         # 사용 가이드
```

### 옵션 B — provider 통합 모듈

```
src/rag_chatbot/
  unified/
  ├── main.py           # 사용자가 --provider 선택
  ├── _graphrag_backend.py
  ├── _lightrag_backend.py
  └── README.md
```

**1차 진행**: 옵션 A (variant 별 디렉토리) — 기존 패턴 일치 + 분리 명확.
사용자가 자기 변형만 골라 사용 가능.

## 6.1 Ollama 의 실제 위치 — 정직한 평가

E0 smoke test 결과로 *"동작은 함"* 이 입증됐지만, *실용 운영* 관점에서 평가:

| 측면 | 결과 |
|---|---|
| **인덱싱 시간** | 1KB → 250s. 100KB 비례 시 **~7시간** (Mac M1 CPU 기준). GPU 사용 시 단축 가능하나 검증 안 됨 |
| **Query 시간** | 30-80s/query (4 mode) — Groq 의 ~5s 대비 **10배+ 느림** |
| **응답 품질** | E0 정성 확인 OK — 정량 비교는 E3 평가 결과 보고 |
| **비용** | 0 (완전 로컬) |
| **프라이버시** | 외부 API 호출 없음 |

→ **메인 권장 X**. *프라이버시 우선* 또는 *외부 API 사용 불가* 환경의 niche 옵션.

옛 GraphRAG + Ollama (docs/refactor/15) 가 entity extraction 단계 fail 였던
것과 달리 LightRAG 는 *동작* — 이건 가설 ("LightRAG = Ollama-friendly") 검증
의의 있음. 단 *실용성* 은 별개.

**메인 흐름**: Groq (default) + Gemini (fallback).

**Ollama 변형 보존 이유**:
- *동작 검증* 자체가 portfolio 가치 (LightRAG 의 plug-and-play 입증)
- 프라이버시 niche 사용자 / 로컬 운영 가능성 명시
- E3 평가 결과 보고 폐기 여부 결정 — 정확도가 Groq 와 큰 차이 없으면 *프라이버시
  옵션* 으로 가치, 30%+ 떨어지면 폐기

## 7. 예상 결과 (가설)

E2 진행 후 평가 결과 예측 — *수치는 가설*, 실제 측정 시 검증:

| 변형 | retrieval 정확도 | latency | cost | 강점 |
|---|---|---|---|---|
| GraphRAG + OpenAI | ⭐⭐⭐⭐⭐ | ~3s | $0.001/q | community summary 강함 |
| GraphRAG + Groq | ⭐⭐⭐⭐ | ~5s | 0 | 무료 + 빠름 |
| GraphRAG + Gemini | ⭐⭐⭐ | ~10s | 0 | 무료, rate-limit 신경 |
| LightRAG + Ollama | ⭐⭐⭐ | ~50s | 0 | 완전 로컬, 프라이버시 |
| LightRAG + Groq | ⭐⭐⭐⭐ | ~5s | 0 | **best 무료 옵션 예상** |
| LightRAG + Gemini | ⭐⭐⭐ | ~15s | 0 | 무료, 단순 |

→ **결정 expected**: LightRAG + Groq 가 무료 권장 default. OpenAI 는 정확도가 *추가* 비용 가치 있을 때만.

## 8. 실패 시 fallback

| 실패 시나리오 | fallback |
|---|---|
| LightRAG + Groq 인덱싱 fail | LightRAG + Gemini |
| LightRAG 응답 품질 < GraphRAG 30% 차이 | LightRAG 폐기, GraphRAG 만 유지 |
| 평가 metric 일관성 안 나옴 | golden 질문 추가 + 재측정 |
| 의존성 충돌 해결 안 됨 | LightRAG 단독 venv 만 보존, 통합 X |

## 9. E2 단계 — 실행 계획

E1 (이 문서) 머지 후 E2 진행:

### E2-1: 의존성 환경 분리
- 별도 venv 가이드 추가 (`docs/setup_lightrag_env.md`)
- `pyproject.toml` 에 `[lightrag]` extra 등록

### E2-2: `src/rag_chatbot/lightrag_variant/` 신설
- `main.py` — Gradio + LightRAG (PR-B 의 llm_provider 와 연동)
- `indexing/` 디렉토리
- `README.md`

### E2-3: `evaluate.py` 에 lightrag 통합
- `--provider lightrag-ollama|lightrag-groq|lightrag-gemini` 지원
- run_chatbot 분기 + lru_cache

### E2-4: 인덱싱 실행 (사용자)
- Groq 권장 (시간 + 비용 최적)
- working_dir: `data/model/lightrag_t_1/`

### E2-5: 평가 + `docs/rag_evaluation_results.md` 갱신
- 6 변형 × golden 10 질문 = 60 결과
- 표 + 해석 + 권장안

## 10. 학습 포인트 (선반영)

1. **E0 smoke test 의 가치** — design doc 가 가설 기반 (틀릴 수도 있는) 이었으면
   E1 도 흐릿했을 텐데, *실측 데이터* 위에서 design 정확도 ↑.
2. **API 차이 vs 본질 차이** — GraphRAG / LightRAG 모두 entity-extraction RAG.
   API 갈아끼우는 게 *core 차이는 아님* (community summary 같은 추가 단계 정도).
3. **Plug-and-play LLM** — LightRAG 의 ``llm_model_func`` 가 callable 받는 구조
   → 우리 ``llm_provider.py`` 와 자연 호환.

## 관련 docs

- [`refactor/15_ollama_graphrag_compatibility.md`](refactor/15_ollama_graphrag_compatibility.md)
  — 옛 GraphRAG + Ollama 실패 (이 비교의 동기)
- [`rag_evaluation_framework.md`](rag_evaluation_framework.md) — 평가 metric
- [`../examples/lightrag_smoke_test/`](../examples/lightrag_smoke_test/) — E0 결과
- [`../examples/graphrag_input/`](../examples/graphrag_input/) — 인덱싱 input (LightRAG 도 사용)
- (예정) `setup_lightrag_env.md` — venv 분리 가이드
- (예정) `rag_evaluation_results.md` — E2 후 결과 표
