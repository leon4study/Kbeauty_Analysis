"""
File: src/rag_chatbot/lightrag_variant/builder.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
무엇인가 (What)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
provider 별 (groq / gemini) LightRAG 인스턴스 빌드 + 인덱싱 + query
를 한 함수로 캡슐화. ``main.py`` (Gradio) 와 ``tests/rag_eval/evaluate.py`` 가
이 모듈을 import 해서 사용.

왜 있는가 (Why)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- LightRAG 의 ``LightRAG()`` 인스턴스화에 provider 별 llm_func + embedding_func
  + working_dir 조합이 다름. 세 곳 (main, evaluate, 인덱싱 스크립트) 에서 같은
  로직 중복 안 되게 단일 진입점.
- provider 별 *embedding 모델 차원이 달라* working_dir 분리 필수 (옛 GraphRAG
  의 차원 mismatch issue 와 동일). ``working_dir_for(provider)`` 가 이 정책.
- 우리 ``src/util/llm_provider.py`` (PR-B 의 sync Groq/Gemini fallback) 와는
  *별개* — LightRAG 는 async callable 받는 구조라 ``lightrag.llm.openai`` /
  ``lightrag.llm.ollama`` 의 async 함수 직접 사용. 단 같은 env (``GROQ_API_KEY``,
  ``GEMINI_API_KEY``) 활용.

어디서 쓰이는가 (Where)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- ``src/rag_chatbot/lightrag_variant/main.py`` — Gradio entry
- ``src/rag_chatbot/lightrag_variant/index_kbeauty.py`` — 인덱싱 1회 스크립트
- ``tests/rag_eval/evaluate.py`` — ``--provider lightrag-*`` 분기

언제 (When)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- ``build_lightrag(provider)`` — 인덱싱 또는 query 직전 매번 호출 (lru_cache 권장).
- ``working_dir_for(provider)`` — 인덱싱 / query 의 storage 경로 결정.

사용법 (How)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    import asyncio
    from rag_chatbot.lightrag_variant.builder import (
        build_lightrag, query_lightrag,
    )
    from lightrag import QueryParam

    async def main():
        rag = await build_lightrag("groq")
        response = await query_lightrag(rag, "건성 피부 보습 크림 추천",
                                          mode="hybrid")
        print(response)

    asyncio.run(main())

설계 노트
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- *async API* — LightRAG 가 async 라 wrapper 도 async.
- *provider 별 embedding 차원 다름* → working_dir 격리 필수:
  - groq (Groq 가 chat 만 제공 → 로컬 Ollama bge-m3 fallback): 1024 dim
  - gemini (text-embedding-004): 768 dim
- *API key 미설정 시 명확한 에러* — 사용자 친화 fallback 메시지.
- *Lazy import* (lightrag 패키지) — 모듈 로드 시 의존성 부재해도 다른 곳 (util
  등) import 깨지지 않게.

관련 파일 (Related)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- src/util/llm_provider.py  ← Groq/Gemini API key 환경변수 공유
- docs/lightrag_comparison_design.md  ← provider 별 시간/비용 estimate
- docs/setup_lightrag_env.md  ← 별도 venv 셋업 (`lightrag-hku` 설치 필요)
- examples/lightrag_smoke_test/  ← E0 검증 결과
"""
from __future__ import annotations

import os
from functools import partial
from pathlib import Path
from typing import Any, Literal

# REPO_ROOT 기준 portable path
_HERE = Path(__file__).resolve()
REPO_ROOT = next(p for p in _HERE.parents if (p / ".git").is_dir())

# provider 별 storage 경로 — embedding 차원 다르면 mismatch 라 격리 필수.
_WORKING_DIRS_BASE = REPO_ROOT / "data" / "model"

ProviderName = Literal["groq", "gemini"]


def working_dir_for(provider: ProviderName) -> Path:
    """provider 별 LightRAG storage 경로 — embedding 차원 충돌 회피 위해 격리.

    Args:
        provider: ``"groq"`` / ``"gemini"``.

    Returns:
        ``data/model/lightrag_<provider>/`` 절대 경로.
    """
    return _WORKING_DIRS_BASE / f"lightrag_{provider}"


# Groq / Gemini 의 OpenAI-compatible base_url.
_GROQ_BASE = "https://api.groq.com/openai/v1"
_GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/openai"

# provider 별 LLM 모델 default — env override 가능.
_DEFAULT_LLM_MODELS = {
    "groq": "llama-3.3-70b-versatile",
    "gemini": "gemini-flash-lite-latest",
}

# provider 별 embedding 모델 + 차원.
# Groq: chat 만 제공 → bge-m3 (Ollama) 로 fallback.
# Gemini: OpenAI-compat endpoint 에서 text-embedding-004 가 404 (2026-05 검증).
#   → 둘 다 로컬 Ollama bge-m3 (1024 dim) 통일. 차원 일관 → 두 인덱스 호환 가능.
_DEFAULT_EMBED_MODELS = {
    "groq":   ("bge-m3", 1024),
    "gemini": ("bge-m3", 1024),
}


async def build_lightrag(provider: ProviderName):
    """provider 별 LightRAG 인스턴스 생성 + storage 초기화.

    Args:
        provider: ``"groq"`` / ``"gemini"``.

    Returns:
        초기화된 ``LightRAG`` 객체 (``ainsert`` / ``aquery`` 가능).

    Raises:
        EnvironmentError: 필수 API key 미설정 시 (Groq/Gemini 경우).
        ImportError: ``lightrag-hku`` 미설치 시 (별도 venv 안 들어옴).

    Note:
        호출부에서 ``functools.lru_cache`` 로 wrap 권장 — 매 query 마다 storage
        다시 로드 안 하도록.
    """
    # Lazy import — lightrag 안 깔린 환경에서도 다른 모듈 import 안 깨지게.
    try:
        from lightrag import LightRAG
        from lightrag.llm.ollama import ollama_embed   # Groq 의 embedding fallback 용
        from lightrag.llm.openai import openai_complete_if_cache
        from lightrag.utils import EmbeddingFunc
    except ImportError as e:
        raise ImportError(
            f"lightrag-hku 미설치: {e}\n"
            f"→ docs/setup_lightrag_env.md 참고 (별도 venv + pip install -e '.[lightrag]')"
        ) from e

    working_dir = working_dir_for(provider)
    working_dir.mkdir(parents=True, exist_ok=True)

    llm_model = os.getenv(f"LIGHTRAG_LLM_{provider.upper()}", _DEFAULT_LLM_MODELS[provider])
    embed_model, embed_dim = _DEFAULT_EMBED_MODELS[provider]

    # ─── provider 별 LLM func ───
    # LightRAG 가 ``llm_model_func(prompt, system_prompt=..., ...)`` 으로 호출 — prompt
    # 가 첫 positional 인자. ``openai_complete_if_cache`` 는 ``(model, prompt, ...)``
    # 라 첫 인자가 model. 직접 넘기면 prompt 가 model 자리에 들어가 TypeError.
    # → wrapper 함수로 model + api_key + base_url 명시적 closure.
    if provider == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GROQ_API_KEY 미설정. .env 에 추가: https://console.groq.com 무료 발급."
            )
        base_url = _GROQ_BASE

    elif provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GEMINI_API_KEY 미설정. .env 에 추가: https://aistudio.google.com 무료 발급."
            )
        base_url = _GEMINI_BASE

    else:
        raise ValueError(f"알 수 없는 provider: {provider!r} (groq/gemini 중 하나)")

    # OpenAI-compat endpoint 공통 wrapper. LightRAG 의 ``llm_model_func`` 시그니처
    # 에 맞춰 prompt 만 positional, 나머지는 keyword 로 받음.
    async def llm_model_func(prompt, system_prompt=None, history_messages=None, **kwargs):
        return await openai_complete_if_cache(
            llm_model,
            prompt,
            system_prompt=system_prompt,
            history_messages=history_messages or [],
            api_key=api_key,
            base_url=base_url,
            **kwargs,
        )

    # llm_model_kwargs 는 wrapper 가 다 처리하므로 비움.
    llm_kwargs: dict = {}

    # ─── embedding func — 모든 provider 가 로컬 Ollama bge-m3 통일 ───
    # Groq: chat 만 제공 → embedding 외부 필요.
    # Gemini: OpenAI-compat embedding endpoint 가 bge-m3 / text-embedding-004
    #   둘 다 404 (2026-05 검증). 로컬 fallback 이 안정적.
    # 차원 1024 통일 → working_dir 간 호환 가능.
    embed_func_inner = partial(
        ollama_embed,
        embed_model=embed_model,
        host="http://localhost:11434",
    )

    embedding_func = EmbeddingFunc(
        embedding_dim=embed_dim,
        max_token_size=8192,
        func=embed_func_inner,
    )

    rag = LightRAG(
        working_dir=str(working_dir),
        llm_model_func=llm_model_func,
        llm_model_name=llm_model,
        summary_max_tokens=8192,
        llm_model_kwargs=llm_kwargs,
        embedding_func=embedding_func,
        # 무료 한도 보호 (default 16 worker 면 즉시 초과):
        # - Gemini Flash Lite: 15 RPM/분 → 2 worker 직렬화
        # - Groq Llama 3.3 70B: 12k TPM/분 (chunk ~6k 토큰) → 2 worker 직렬화
        # 인덱싱 시간 늘지만 100KB 입력 기준 여전히 ~30분 내.
        llm_model_max_async=2,
    )
    await rag.initialize_storages()
    return rag


async def insert_text(rag, text: str) -> None:
    """text 를 LightRAG 인덱스에 insert (entity extraction + 저장).

    Args:
        rag: ``build_lightrag()`` 반환 인스턴스.
        text: 인덱싱할 텍스트 (JSON / plain text / markdown 등).

    Note:
        entity extraction 이 LLM 호출 N번 — Ollama gemma2 의 경우 ~수 시간 (100KB
        기준). Groq/Gemini 면 ~수 분.
    """
    await rag.ainsert(text)


async def query_lightrag(rag, question: str, mode: str = "hybrid") -> str:
    """LightRAG 인스턴스에 query → 응답 문자열 반환.

    Args:
        rag: ``build_lightrag()`` 반환 인스턴스.
        question: 자연어 질문.
        mode: ``"naive"`` / ``"local"`` / ``"global"`` / ``"hybrid"``.
            - ``naive``: embedding 만 (entity graph 우회) — 가장 빠름.
            - ``local``: entity neighbor 위주.
            - ``global``: community 위주.
            - ``hybrid``: local + global 결합 — 정확도 best 추정.

    Returns:
        응답 텍스트.
    """
    # Lazy import (위 build_lightrag 와 동일 이유).
    from lightrag import QueryParam

    response = await rag.aquery(question, param=QueryParam(mode=mode))
    return str(response)
