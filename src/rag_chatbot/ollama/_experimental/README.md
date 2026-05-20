# _experimental/ — 미완성/검증 안 된 실험 변종 모음

`src/rag_chatbot/ollama/` 의 메인 흐름 (`gradio_rag_ch7.py`) 과 분리해서
*시도했지만 완성 못 한* 코드 보존. *현재 어디서도 import 안 됨* 보장.

## 왜 _experimental/ 인가

- 사용자 feedback 메모리 "Variants = experiment branches, keep in-tree" —
  코드는 폴더에서 보여야 의도 명확
- 옛 변종을 git 안에서 sketching 했던 흔적 → 학습 가치 + 부분 재사용 가능
- 메인 모듈 폴더 평면에 두면 *작동하는 코드와 혼동* — `_` prefix 로 한눈에 구분

## 파일

| 파일 | 정체 | 미완성 이유 |
|---|---|---|
| `OllamaLLM.py` | `BaseOllama` (llama_index) 를 확장한 custom Ollama wrapper. httpx 직접 사용으로 `/api/chat` raw 호출 + json_mode / timeout / context_window 세밀 제어. | 3 심볼 import 누락: `DEFAULT_NUM_OUTPUTS`, `llm_chat_callback`, `get_additional_kwargs`. 실행 검증 안 됨. 현재 callers 0. |

## OllamaLLM.py 상세

### 의도

`llama_index.llms.ollama.Ollama` 기본 wrapper 가 timeout/json_mode 세밀 제어
부족 → httpx 로 raw HTTP 호출하는 custom wrapper. 옛 Ollama 인덱싱 안정성
시도의 일환 (`docs/refactor/15_ollama_graphrag_compatibility.md` 참조).

### 미완성 흔적

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

llama_index 최신 API 기준 필요 import (검증 필요 — API 버전마다 위치 다름):

```python
from llama_index.core.constants import DEFAULT_NUM_OUTPUTS
from llama_index.core.llms.callbacks import llm_chat_callback
from llama_index.core.base.llms.generic_utils import get_additional_kwargs
```

또한 *왜 custom wrapper 가 필요한지* 재검토 필요:
- 최신 `llama_index.llms.ollama.Ollama` 가 이미 timeout / json_mode 지원 →
  custom wrapper 필요 없을 수 있음
- 옛 시도 시점 (2025-02 추정) 의 llama_index 버전 한계였을 가능성

### 폐기 안 한 이유

- 코드 자체는 *raw HTTP 제어 패턴* 학습 가치 있음 (httpx + Ollama API 직접 사용)
- 향후 더 세밀한 제어 필요 시 (예: streaming, custom retry) base 로 활용 가능
- 메인 흐름과 분리됐으니 *방해* 안 함

## 메인 흐름

활성 챗봇은 표준 `llama_index.llms.ollama.Ollama` 사용:

```python
# src/rag_chatbot/ollama/gradio_rag_ch7.py:91
Settings.llm = Ollama(model="gemma2", base_url=..., request_timeout=...)
```

`_experimental/` 의 custom wrapper 가 *필요* 한 시나리오는 현재 없음.

## 관련 docs

- [`../README.md`](../README.md) — Ollama 챗봇 메인 사용 가이드
- [`../../../docs/refactor/15_ollama_graphrag_compatibility.md`](../../../docs/refactor/15_ollama_graphrag_compatibility.md)
  — Ollama × GraphRAG 시도 실패 기록 (이 모듈도 그 흔적의 일부)
- [`../../../docs/refactor/09_ollama_rag_variants.md`](../../../docs/refactor/09_ollama_rag_variants.md)
  — Ollama 챗봇 ch1~ch8 변종 카탈로그
