# Ollama RAG 변종 정리

`src/rag_chatbot/ollama/` 안에 ch1 ~ ch8 progressive variants + 별도 stack 시도 + LLM wrapper 두 버전이 쌓여있던 것을 한 canonical + 한 별개 stack 보존본으로 줄였다.

## 배경 / 의도

K-beauty 분석 데이터를 GraphRAG 로 인덱싱한 결과 (LanceDB) 에 자연어 질문을 던지는 챗봇을 만들기 위한 시도. **로컬 Ollama** 로 LLM 비용을 줄이는 게 목표 (메인 챗봇 `cosmetic_rag_chat/` 은 OpenAI cloud 사용).

`gradio_rag_chN.py` 라는 이름으로 N 을 늘려가며 한 챗봇을 점진적으로 다듬은 흔적이 ch1 ~ ch8 까지 누적됐고, 중간에 한 번 LangChain stack 으로 갈라진 가지(ch3) 가 있었다. 또 `OllamaLLM.py` (23 lines) 와 `OllamaLLM2.py` (110 lines) 두 버전의 LLM wrapper.

## 시도된 변종

### Gradio RAG 진화 (LlamaIndex + LanceDB + Ollama 같은 stack)

| Variant | lines | 특징 / 시도 | 다음 변종 대비 변화 | 처분 |
|---------|------:|------------|---------------------|------|
| `gradio_rag_ch1.py` | 82 | 기본 골격 — Ollama + LanceDB + LlamaIndex + Gradio Interface | (시작점) | ❌ 폐기 |
| `gradio_rag_ch2.py` | 0 | **빈 파일** — placeholder, 작성 시작 안 함 | — | ❌ 폐기 |
| `gradio_rag_ch4.py` | 83 | ch1과 거의 동일 | 미세 차이 | ❌ 폐기 |
| `gradio_rag_ch5.py` | 90 | imports 정리 | +7 lines | ❌ 폐기 |
| `gradio_rag_ch6.py` | 121 | 주석 헤더 (YAML 기반 RAG 설명) | +31 lines | ❌ 폐기 |
| `gradio_rag_ch7.py` | 117 | **ChatInterface (multimodal)** + 파일 업로드 + parquet→txt 변환 | 큰 변화 (`gr.Interface` → `gr.ChatInterface`, ch6↔ch7 = 15줄) | ✅ canonical .py |
| `gradio_rag_ch7.ipynb` | (~117) | ch7.py 와 95% 동일 — 출력 보면서 개발하던 버전 | 동일 코드 | ❌ 폐기 (.py 가 있음) |
| `gradio_rag_ch8.ipynb` | 13 cells | LanceDB graph 데이터 더 깊이 활용 (relationship_df, indexes dict) | 별개 진화 (ch7과 22% 유사) | ✅ 보존 (별개 시도) |
| `rag_chat_t1.py` | 23 | test scratch | — | ❌ 폐기 |

**ch1 ↔ ch7 diff**: 100줄 (큰 진화)
**ch6 ↔ ch7 diff**: 15줄 (마지막 큰 도약 — UI 가 `Interface` → `ChatInterface` 로 바뀜)

### LangChain 변종 (ch3)

| Variant | lines | 특징 |
|---------|------:|------|
| `gradio_rag_ch3.py` | 58 | LangChain + FAISS + ChatOpenAI(`gpt-3.5`) — **다른 스택**. 사용자 업로드 문서만 사용 (GraphRAG 안 씀). title은 "Ollama 활용" 인데 코드는 OpenAI cloud — **마이그레이션 미완성** |

처분: **`~/GitStudy/utils/legacy_rag/langchain_variant.py`** 로 보존 (다른 stack 학습 자료)

### LLM wrapper

| Variant | lines | 특징 |
|---------|------:|------|
| `OllamaLLM.py` (옛) | 23 | 기본 wrapper |
| `OllamaLLM2.py` | 110 | `BaseOllama` 확장 → CustomOllamaLLM (httpx 직접, timeout, json_mode, context_window 등). ⚠️ `DEFAULT_NUM_OUTPUTS` / `llm_chat_callback` / `get_additional_kwargs` import 누락 — chat 호출까지 검증 안 됨 |

처분: 옛 23줄 폐기, `OllamaLLM2.py` → `OllamaLLM.py` 이름 회수 (단일 wrapper).

## 최종 채택 + 이유

### `gradio_rag_ch7.py`
- ch1 → ch7 진화의 마지막 .py 단계 (ch6 → ch7에서 `gr.ChatInterface(multimodal)` 로 큰 도약)
- 출력 확인용이었던 `.ipynb` 는 동일 코드라 .py 만 남김
- **Canonical 결정 후 추가로 다음을 적용**:
  - 모듈/함수 docstring (스택 설명, 가정, 확장 힌트)
  - stale `Data_4` 경로 → `util.repo_paths.DATA` 기반
  - `if __name__ == "__main__":` guard (import 만으로 Gradio 실행 안 되게)

### `gradio_rag_ch8.ipynb` 별도 보존
- ch7 와 22% 유사 = **다른 진화 가지**. relationship_df, VectorStoreIndex.from_vector_store 등 LanceDB graph 데이터 더 깊이 활용
- .ipynb 형태 유지 (출력 보면서 실험적 사용 의도)

### `OllamaLLM.py` (옛 OllamaLLM2 가 회수한 이름)
- 단일 wrapper만 남김
- 알려진 미완성 (import 누락) 은 docstring 에 명시 — 사용 시 수정 필요

### `check_db.ipynb` 보존
- LanceDB 검증 도구. 챗봇 만드는 동안 DB 상태 확인용 — 현재도 유효

## canonical 위치

```
src/rag_chatbot/ollama/
├── __init__.py
├── OllamaLLM.py            (CustomOllamaLLM wrapper, 미완성 docstring 명시)
├── check_db.ipynb          (LanceDB 검증 도구)
├── gradio_rag_ch7.py       (메인 Ollama RAG 챗봇 — Gradio ChatInterface)
└── gradio_rag_ch8.ipynb    (ch7 다음 단계 실험 — 별개 진화 가지)
```

## 학습 노트 보존 위치

```
~/GitStudy/utils/legacy_rag/
└── langchain_variant.py    (옛 ch3.py — LangChain + FAISS stack 시도)
```

폐기된 ch1/4/5/6.py 는 git history 에만 남김. 진화 흔적은 이 문서로 충분.

## 학습 포인트

1. **Variant naming**: `chN` 식 숫자 증가는 진화 흐름은 보여주지만 **무엇이 어떻게 바뀌었는지** 는 안 보임. 의미 있는 commit message + 적은 수의 의미 있는 파일이 더 나음.
2. **다른 stack 시도는 `_variant.py` 같이 명확한 이름으로 분리**. ch3가 LangChain 인 게 파일명에 안 드러나서 헷갈렸음.
3. **`gr.Interface` → `gr.ChatInterface` (multimodal)** 는 RAG 챗봇에서 의미 있는 도약 — 파일 업로드 + 멀티턴 대화 지원.
4. **LLM wrapper 확장은 작은 일 아님**: `BaseOllama` extend 시 callback / metadata / chat 시그니처 등 LlamaIndex 내부 contract 알아야 함 (OllamaLLM2의 미완성이 그 증거).
5. **노트북과 .py 동시 보존은 90%+ 같은 코드면 둘 중 하나로 충분**. 출력을 보존하고 싶으면 .ipynb, 실행/배포면 .py.

## 관련 commits

- `3a99a56` — refactor(rag_chatbot/ollama): keep ch7 + ch8.ipynb, drop ch1/4/5/6 progressive variants
- (이전) `2d248cd` — rag_chatbot 0209 → cosmetic 진화 정리 (`08_chatbot_v1_v2.md` 참고)