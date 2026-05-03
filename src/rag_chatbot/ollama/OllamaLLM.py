"""Ollama LLM custom wrapper — base ``llama_index.llms.ollama.Ollama`` 확장.

목적:
- 기본 ``Ollama`` 클래스보다 더 세밀한 제어 (timeout, json_mode, temperature
  bounds, context window 등) 가 필요해서 만든 wrapper
- ``httpx`` 직접 사용해서 ``/api/chat`` endpoint 호출 (LlamaIndex 의 기본
  Ollama wrapper 대신 raw HTTP 제어)

⚠️ 알려진 미완성 (향후 손볼 필요):
- ``DEFAULT_NUM_OUTPUTS`` / ``llm_chat_callback`` / ``get_additional_kwargs``
  심볼이 import 안 되어 있음 — 그대로 실행하면 ``NameError``.
- 실제로 chat 호출까지 가본 흔적은 없음 (실행 검증 안 됨).
- 사용하려면 ``llama_index.core.llms.base`` /
  ``llama_index.core.llms.callbacks`` 등에서 누락 심볼 추가 필요.

원래 이름 ``OllamaLLM2.py`` (구버전 ``OllamaLLM.py`` 23줄을 확장한 v2) 였으나
구버전 폐기 후 단일 wrapper로 정리하면서 이름을 ``OllamaLLM.py`` 로 회수.
"""
from typing import Any, Dict, Sequence

import httpx
from httpx import Timeout
from llama_index.core.llms import (
    ChatMessage,
    ChatResponse,
    LLMMetadata,
    MessageRole,
)
from llama_index.llms.ollama import Ollama as BaseOllama
from pydantic import Field


class CustomOllamaLLM(BaseOllama):
    """``BaseOllama`` 확장 — timeout/json_mode/context_window 등 세밀 옵션 추가."""

    base_url: str = Field(
        default="http://localhost:11434",
        description="Base url the model is hosted under.",
    )
    model: str = Field(description="The Ollama model to use.")
    temperature: float = Field(
        default=0.75,
        description="The temperature to use for sampling.",
        gte=0.0,
        lte=1.0,
    )
    context_window: int = Field(
        default=4096,  # 기본 context_window 설정 (예시)
        description="The maximum number of context tokens for the model.",
        gt=0,
    )
    request_timeout: float = Field(
        default=60.0,
        description="The timeout for making http request to Ollama API server",
    )
    prompt_key: str = Field(
        default="prompt", description="The key to use for the prompt in API calls."
    )
    json_mode: bool = Field(
        default=False,
        description="Whether to use JSON mode for the Ollama API.",
    )
    additional_kwargs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional model parameters for the Ollama API.",
    )

    @classmethod
    def class_name(cls) -> str:
        return "Ollama_llm"

    @property
    def metadata(self) -> LLMMetadata:
        """LLM 메타데이터 반환."""
        return LLMMetadata(
            context_window=self.context_window,
            num_output=DEFAULT_NUM_OUTPUTS,
            model_name=self.model,
            is_chat_model=True,  # Ollama는 모든 모델에 대해 채팅 API를 지원
        )

    @property
    def _model_kwargs(self) -> Dict[str, Any]:
        base_kwargs = {
            "temperature": self.temperature,
            "num_ctx": self.context_window,
        }
        return {
            **base_kwargs,
            **self.additional_kwargs,
        }

    @llm_chat_callback()
    def chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponse:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": message.role.value,
                    "content": message.content,
                    **message.additional_kwargs,
                }
                for message in messages
            ],
            "options": self._model_kwargs,
            "stream": False,
            **kwargs,
        }

        if self.json_mode:
            payload["format"] = "json"

        with httpx.Client(timeout=Timeout(self.request_timeout)) as client:
            response = client.post(
                url=f"{self.base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            raw = response.json()
            message = raw["message"]
            return ChatResponse(
                message=ChatMessage(
                    content=message.get("content"),
                    role=MessageRole(message.get("role")),
                    additional_kwargs=get_additional_kwargs(
                        message, ("content", "role")
                    ),
                ),
                raw=raw,
                additional_kwargs=get_additional_kwargs(raw, ("message",)),
            )
