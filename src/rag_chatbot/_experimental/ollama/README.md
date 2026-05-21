# _experimental/ollama/ — Ollama 변형 (archived experiment)

GraphRAG + Ollama 로컬 챗봇 *시도*. 옛 위치 `src/rag_chatbot/ollama/` 에서
`_experimental/ollama/` 로 이동.

## 왜 _experimental/ 로 이동했나

- 메인 챗봇 = `src/rag_chatbot/cosmetic_rag_chat/` (GraphRAG + OpenAI)
- Ollama 변형은 *호환성 issue + 실용성 ↓* 로 거의 안 씀:
  - **GraphRAG + Ollama**: entity extraction 단계 fail
    ([`docs/refactor/15`](../../../../docs/refactor/15_ollama_graphrag_compatibility.md))
  - **LightRAG + Ollama** (E0 검증): 동작은 하지만 100KB 인덱싱 ~7시간 추정
    ([`docs/lightrag_comparison_design.md`](../../../../docs/lightrag_comparison_design.md) §6.1)
- 메인 폴더에 잘 안 쓰는 모듈 두면 새 사용자 혼동 → `_experimental/` 으로 격리

## 파일

| 파일 | 정체 | 상태 |
|---|---|---|
| `gradio_rag_ch7.py` | Gradio + Ollama (gemma2) 메인 챗봇 (ch1~ch8 progressive 의 종점) | 동작 X 검증 (인덱싱 미진) |
| `gradio_rag_ch8.ipynb` | LanceDB graph 데이터 깊이 활용 실험 | 실험 |
| `check_db.ipynb` | LanceDB 검증 도구 (테이블/entity 미리보기) | 도구 |
| `OllamaLLM.py` | LlamaIndex 용 custom Ollama wrapper (httpx 직접) | 미완성 — 3 import 누락, callers 0 |

## OllamaLLM.py — 미완성

`BaseOllama` (llama_index) 를 확장해 httpx 로 `/api/chat` raw 호출하는 wrapper.

3 심볼 import 누락 → 실행 시 `NameError`:

```python
@llm_chat_callback()       # ← undefined (line 93)
def chat(self, ...):
    return ChatResponse(
        message=ChatMessage(
            additional_kwargs=get_additional_kwargs(  # ← undefined (line 125, 130)
                ...
            ),
        ),
    )

@property
def metadata(self) -> LLMMetadata:
    return LLMMetadata(
        num_output=DEFAULT_NUM_OUTPUTS,   # ← undefined (line 77)
        ...
    )
```

### 만약 다시 살리려면

llama_index 최신 API 기준 (검증 필요):

```python
from llama_index.core.constants import DEFAULT_NUM_OUTPUTS
from llama_index.core.llms.callbacks import llm_chat_callback
from llama_index.core.base.llms.generic_utils import get_additional_kwargs
```

`llama_index.llms.ollama.Ollama` 가 이미 timeout / json_mode 지원하므로 custom
wrapper 필요 없을 수도 있음.

## 옛 위치 호환성

**기존 명령어는 더 이상 동작 X**:
```bash
python -m src.rag_chatbot.ollama.gradio_rag_ch7   # ← 옛 경로 (X)
```

**새 경로** (사용 비권장):
```bash
python -m src.rag_chatbot._experimental.ollama.gradio_rag_ch7
```

→ 권장은 **메인 챗봇** ([`../../cosmetic_rag_chat/`](../../cosmetic_rag_chat/))
또는 **LightRAG 변형** ([`../../lightrag_variant/`](../../lightrag_variant/)).

## 보존 이유

- 동작 검증 *흔적* 자체가 portfolio 가치 (옛 GraphRAG + Ollama 호환성 한계 입증)
- 향후 더 큰 모델 (Llama 3.3 70B + 로컬 GPU) 환경 생기면 재시도 가능
- ch1~ch8 progressive iteration 학습 결과 보존

## 관련 docs

- [`../../cosmetic_rag_chat/README.md`](../../cosmetic_rag_chat/README.md) — 메인 챗봇 (OpenAI GraphRAG)
- [`../../lightrag_variant/README.md`](../../lightrag_variant/README.md) — LightRAG 변형 (실험)
- [`../../../../docs/refactor/15_ollama_graphrag_compatibility.md`](../../../../docs/refactor/15_ollama_graphrag_compatibility.md) — GraphRAG + Ollama 시도 실패
- [`../../../../docs/refactor/09_ollama_rag_variants.md`](../../../../docs/refactor/09_ollama_rag_variants.md) — ch1~ch8 변종 카탈로그
- [`../../../../docs/lightrag_comparison_design.md`](../../../../docs/lightrag_comparison_design.md) §6.1 — Ollama 실용성 평가
