# Ollama RAG 챗봇

K-beauty GraphRAG 인덱싱 결과 (LanceDB) 에 자연어 질문을 던지는 챗봇. **로컬 Ollama** 로 LLM 비용을 줄이는 게 목표 (메인 챗봇 [`../cosmetic_rag_chat/`](../cosmetic_rag_chat/) 은 OpenAI cloud 사용).

## canonical 파일

| 파일 | 무엇을 함 |
|---|---|
| `gradio_rag_ch7.py` | 메인 챗봇 — Gradio `ChatInterface(multimodal)` + LanceDB + LlamaIndex + Ollama. 파일 업로드 + 멀티턴 대화 지원. ch1→ch7 progressive iteration 의 마지막 단계 |
| `gradio_rag_ch8.ipynb` | ch7 다음 별개 진화 가지 — LanceDB graph 데이터를 더 깊이 활용 (relationship_df, indexes dict 등). ch7 와 22% 유사 |
| `OllamaLLM.py` | LlamaIndex 용 Custom Ollama LLM wrapper (httpx 직접, timeout, json_mode, context_window). ⚠️ 알려진 미완성 (import 누락) — 사용 전 docstring 확인 |
| `check_db.ipynb` | LanceDB 검증 도구 — 테이블 목록, entity-description 미리보기 |

## 실행

```bash
# Ollama 데몬 (localhost:11434) 실행 + GraphRAG 인덱싱 결과 (data/model/graphrag_t_2/output/lancedb) 준비된 상태에서
python -m src.rag_chatbot.ollama.gradio_rag_ch7
```

## 변종 카탈로그 (폐기/외부 보존된 것 포함)

| 변종 | 가설/차이 | 처분 |
|---|---|---|
| `gradio_rag_ch1.py` (82줄) | 기본 골격 — Ollama + LanceDB + LlamaIndex + `gr.Interface` | 폐기 (git show `3a99a56^:...` 으로 복원 가능) |
| `gradio_rag_ch2.py` | 빈 placeholder | 폐기 |
| `gradio_rag_ch4.py` (83줄) | ch1과 거의 동일, 미세 차이 | 폐기 |
| `gradio_rag_ch5.py` (90줄) | imports 정리 | 폐기 |
| `gradio_rag_ch6.py` (121줄) | YAML 기반 RAG 주석 헤더 추가 | 폐기 |
| `gradio_rag_ch7.ipynb` | ch7.py 와 95% 동일, 출력 보면서 개발용 | 폐기 (.py 가 충분) |
| `gradio_rag_ch3.py` (58줄) | **다른 stack** — LangChain + FAISS + ChatOpenAI(gpt-3.5). title은 Ollama 인데 코드는 OpenAI cloud → 마이그레이션 미완성 | `~/GitStudy/utils/legacy_rag/langchain_variant.py` 보존 |
| `OllamaLLM.py` (옛 v1, 23줄) | 기본 wrapper | 폐기. v2 가 `OllamaLLM.py` 이름 회수 (단일 wrapper) |
| `rag_chat_t1.py` | test scratch | 폐기 |

## 진화 흐름

```
ch1 (82, 기본)
  ↓
ch4 (83, 미세조정)
  ↓
ch5 (90, imports 정리)
  ↓
ch6 (121, RAG 주석 헤더)
  ↓
ch7 (117, gr.Interface → ChatInterface multimodal)  ← canonical .py
  ↓
ch8.ipynb (LanceDB graph 더 깊이 활용)               ← 별개 가지, 보존

[ch3 LangChain 변종 → utils/legacy_rag/langchain_variant.py]
```

**ch1 ↔ ch7 diff = 100줄** (큰 진화), **ch6 ↔ ch7 diff = 15줄** (마지막 큰 도약 — UI multimodal 화).

## 학습 포인트

1. `chN` 식 숫자 증가 네이밍은 진화 흐름은 보여주지만 **무엇이 바뀌었는지** 안 보임 → 의미 있는 commit + 적은 수의 의미 있는 파일이 더 나음
2. 다른 stack 시도는 `_variant.py` 처럼 명확한 이름으로 분리 (ch3 가 LangChain 인 게 파일명에 안 드러나 헷갈렸음)
3. `gr.Interface` → `gr.ChatInterface(multimodal)` 이 RAG 챗봇에서 의미 있는 도약 (파일 업로드 + 멀티턴)
4. LLM wrapper 확장은 작은 일 아님 — `BaseOllama` extend 시 callback / metadata / chat 시그니처 등 LlamaIndex 내부 contract 알아야 (OllamaLLM2 의 미완성이 그 증거)
5. 노트북과 .py 동시 보존은 90%+ 같은 코드면 둘 중 하나로 충분

## 관련 docs

- [../../docs/refactor/09_ollama_rag_variants.md](../../docs/refactor/09_ollama_rag_variants.md) — 자세한 변종 정리 기록
- [../../docs/refactor/EXPERIMENTS_PLAYBOOK.md](../../docs/refactor/EXPERIMENTS_PLAYBOOK.md) — 변종 정리 표준 (이 README 가 패턴 C 의 사례)
