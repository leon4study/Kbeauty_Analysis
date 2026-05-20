"""
File: src/util/llm_provider.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
무엇인가 (What)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
무료/저비용 LLM provider (Groq, Gemini) 간 자동 폴백을 처리하는 단일 함수
`llm_complete(prompt, ...)` 제공. K-Beauty 챗봇이 OpenAI 의존성에서 벗어나 무료
한도 내에서 동작 가능하게 함.

왜 있는가 (Why)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*1) GraphRAG 인덱싱은 OpenAI 가 필수 (entity extraction 품질)* 이지만 *챗봇
   query 단계는 가벼운 LLM 호출* — 무료 provider 로 대체해도 응답 품질 충분.

*2) 무료 한도 활용*:
   - Groq (Llama 3.3 70B): ~1k RPM, ~14k RPD 무료
   - Gemini (Gemini Flash Lite): ~15 RPM, 1.5M TPM 무료
   → 두 개 같이 쓰면 충분.

*3) `LLM_PROVIDER=auto` 모드*: Groq 먼저 시도 → 실패 시 Gemini 폴백. 한쪽이
   rate limit 걸려도 다른 쪽으로 계속 동작.

*4) economic_words 프로젝트 (`/Users/jun/GitStudy/economic_words/src/main.py:151-251`)
   의 검증된 패턴* — 무료 한도 내 1년+ 운영 실적. K-Beauty 챗봇에 동일 패턴 적용.

어디에 쓰이는가 (Where)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- ``src/rag_chatbot/cosmetic_rag_chat/main.py`` — 챗봇 query LLM 호출
- ``src/rag_chatbot/ollama/gradio_rag_ch7.py`` — Ollama 변형 폴백
- ``tests/rag_eval/evaluate.py`` — judge LLM 호출 (예정)

GraphRAG 인덱싱과는 별개 — 인덱싱은 ``settings.yaml`` 의 ``api_base`` 로
Groq 의 OpenAI-compatible endpoint 사용 (코드 변경 X, env 만).

사용법 (How)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    from util.llm_provider import llm_complete

    # 기본: LLM_PROVIDER=auto (Groq → Gemini 폴백)
    response = llm_complete("화장품 추천: 건성 피부에 보습 크림 알려줘")
    print(response)

    # JSON 모드 (structured output)
    json_resp = llm_complete(
        "다음을 JSON 으로: 추천 3개, 이유 1줄씩",
        json_mode=True,
        max_tokens=300,
    )

    # provider 강제
    response = llm_complete(prompt, provider="groq")  # Groq 만 시도

환경 변수 (.env)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    LLM_PROVIDER=auto              # auto / groq / gemini
    GROQ_API_KEY=gsk_...           # https://console.groq.com (무료 가입)
    GEMINI_API_KEY=AIza...         # https://aistudio.google.com (무료 가입)
    GROQ_MODEL=llama-3.3-70b-versatile      # 옵션 (default)
    GEMINI_MODEL=gemini-flash-lite-latest   # 옵션 (default)

설계 노트
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- *Sync 인터페이스* — K-Beauty 챗봇 (Gradio) 이 sync 라 sync httpx Client 사용.
  economic_words 는 async (FastAPI) 라 `httpx.AsyncClient` 였지만 본질은 동일.
- *Provider-별 wrapper 분리* (`_call_groq`, `_call_gemini`) — 각 provider 의
  JSON 형식이 다름 (Groq=OpenAI-compatible, Gemini=Google native). 추가
  provider (Cerebras, Together AI 등) 도 같은 패턴으로 확장.
- *None 반환으로 실패 시그널* — 예외 던지면 호출부가 try/except 잔뜩 필요.
  None 체크 한 줄로 fallback 가능.
- *API key 노출 방지* — 에러 로그에 URL 전체 안 찍음 (HTTP 상태 + 응답 body
  앞 500자만).

관련 파일 (Related)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- /Users/jun/GitStudy/economic_words/src/main.py (line 151-251)
   ← 원본 async 패턴. 본 모듈은 sync 변형.
- docs/rag_evaluation_framework.md
   ← 이 모듈을 사용한 provider 비교 평가 계획.
- docs/refactor/15_ollama_graphrag_compatibility.md
   ← 옛 Ollama 시도 실패 기록. 이 모듈은 그 fallback 의 후속.
"""
from __future__ import annotations

import os
from typing import Literal, Optional

import httpx
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

# ─────────────────────────────────────────────────────────────────────────────
# API key + provider 설정 (env 우선)
# ─────────────────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# LLM_PROVIDER — env 미설정 시 'auto' (Groq 우선 → 실패 시 Gemini 폴백).
# economic_words 와 동일 default. "groq" 또는 "gemini" 단독 강제도 가능.
_VALID_PROVIDERS = ("auto", "groq", "gemini")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto").lower()
if LLM_PROVIDER not in _VALID_PROVIDERS:
    print(
        f"[llm_provider] WARNING: LLM_PROVIDER={LLM_PROVIDER!r} 알 수 없음 "
        f"→ 'auto' 로 폴백. 유효값: {_VALID_PROVIDERS}"
    )
    LLM_PROVIDER = "auto"

# 모델명 — env override 가능.
# Groq 의 llama-3.3-70b-versatile: 무료 한도 ~1k RPM. 더 큰 한도 필요 시
# llama-3.1-8b-instant (~14.4k RPD, 품질 살짝 ↓).
# Gemini 의 gemini-flash-lite-latest: 무료 한도 15 RPM, 1.5M TPM/일.
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")

# Endpoint URL — provider 마다 다른 protocol.
# Groq: OpenAI-compatible (POST /v1/chat/completions)
# Gemini: Google native (POST /v1beta/models/<model>:generateContent)
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}"
    f":generateContent"
)

# 시작 시 활성 provider + key 존재 여부 로깅 — debug 친화.
# (API key 자체는 출력 X, 존재 여부만)
print(f"[llm_provider] LLM_PROVIDER: {LLM_PROVIDER}")
print(f"[llm_provider] GROQ_API_KEY exists: {bool(GROQ_API_KEY)} (model: {GROQ_MODEL})")
print(f"[llm_provider] GEMINI_API_KEY exists: {bool(GEMINI_API_KEY)} (model: {GEMINI_MODEL})")


ProviderName = Literal["auto", "groq", "gemini"]


def _call_groq(
    client: httpx.Client,
    prompt: str,
    max_tokens: int,
    temperature: float,
    json_mode: bool,
    timeout: float,
) -> Optional[str]:
    """Groq 의 OpenAI-compatible endpoint 호출.

    Args:
        client: 재사용할 httpx.Client (connection pool).
        prompt: 사용자 prompt (system+user 분리 안 함 — 단순 모드).
        max_tokens: 응답 최대 토큰.
        temperature: 샘플링 온도 (0=결정적, 1=창의적).
        json_mode: True 면 `response_format={"type":"json_object"}` 전송.
        timeout: HTTP 타임아웃 (sec).

    Returns:
        응답 텍스트 또는 None (key 없음 / HTTP 에러 / parse 실패 시).
    """
    if not GROQ_API_KEY:
        return None
    try:
        payload: dict = {
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if json_mode:
            # OpenAI-compatible JSON mode (Groq 가 그대로 지원).
            payload["response_format"] = {"type": "json_object"}
        resp = client.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json=payload,
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except httpx.HTTPStatusError as e:
        # URL 노출 방지: 상태코드 + 응답 본문 일부만.
        body = (e.response.text or "")[:500]
        print(f"[_call_groq HTTP {e.response.status_code}] {body}")
        return None
    except Exception as e:
        print(f"[_call_groq ERROR] {type(e).__name__}: {str(e)[:200]}")
        return None


def _call_gemini(
    client: httpx.Client,
    prompt: str,
    max_tokens: int,
    temperature: float,
    json_mode: bool,
    timeout: float,
) -> Optional[str]:
    """Google Gemini 의 native endpoint 호출.

    Groq 와 다르게 OpenAI-compatible 아님. ``generationConfig`` 객체로
    parameter 전달 + ``contents`` 배열로 prompt.

    Args:
        client: httpx.Client.
        prompt: 사용자 prompt.
        max_tokens: 응답 최대 토큰.
        temperature: 샘플링 온도.
        json_mode: True 면 `responseMimeType="application/json"` 전송.
        timeout: HTTP 타임아웃 (sec).

    Returns:
        응답 텍스트 또는 None.
    """
    if not GEMINI_API_KEY:
        return None
    try:
        generation_config: dict = {
            "maxOutputTokens": max_tokens,
            "temperature": temperature,
        }
        if json_mode:
            # Gemini 의 JSON mode — responseMimeType 으로 강제.
            generation_config["responseMimeType"] = "application/json"
        resp = client.post(
            GEMINI_URL,
            headers={"x-goog-api-key": GEMINI_API_KEY},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": generation_config,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except httpx.HTTPStatusError as e:
        body = (e.response.text or "")[:500]
        print(f"[_call_gemini HTTP {e.response.status_code}] {body}")
        return None
    except Exception as e:
        print(f"[_call_gemini ERROR] {type(e).__name__}: {str(e)[:200]}")
        return None


def llm_complete(
    prompt: str,
    max_tokens: int = 500,
    temperature: float = 0.4,
    json_mode: bool = False,
    timeout: float = 20.0,
    provider: Optional[ProviderName] = None,
    client: Optional[httpx.Client] = None,
) -> Optional[str]:
    """무료 LLM provider (Groq, Gemini) 자동 폴백 호출.

    `provider` 또는 env `LLM_PROVIDER` 에 따른 라우팅:
    - ``"auto"`` (default): Groq 먼저 시도 → 실패 / 키 없음 → Gemini 폴백
    - ``"groq"``: Groq 단독
    - ``"gemini"``: Gemini 단독

    Args:
        prompt: 사용자 prompt.
        max_tokens: 응답 최대 토큰 (default 500, 챗봇 응답 기준).
        temperature: 0.0 (결정적) ~ 1.0 (창의적). default 0.4 = 약간 창의적.
        json_mode: True 면 LLM 응답을 JSON 으로 강제 (structured output).
        timeout: HTTP 타임아웃 (sec). default 20s — graphrag 의 무거운 쿼리 고려.
        provider: env LLM_PROVIDER override. None 이면 env 값 사용.
        client: 재사용할 httpx.Client. None 이면 함수 안에서 임시 생성.

    Returns:
        응답 텍스트 (성공) 또는 None (모든 provider 실패).

    Examples:
        >>> llm_complete("hello, 한 단어로 인사")
        '안녕하세요'

        >>> llm_complete("brand 3개를 json 으로", json_mode=True, max_tokens=100)
        '{"brands": ["COSRX", "PURITO", "Beauty of Joseon"]}'

        >>> # 강제 Gemini 사용
        >>> llm_complete("test", provider="gemini")
    """
    chosen_provider = (provider or LLM_PROVIDER).lower()
    if chosen_provider not in _VALID_PROVIDERS:
        chosen_provider = "auto"

    # client 없으면 임시 생성 (context manager 로 안전한 close).
    _owns_client = client is None
    if _owns_client:
        client = httpx.Client()

    try:
        # 단일 provider 모드 — 폴백 없이 즉시 반환.
        if chosen_provider == "groq":
            return _call_groq(client, prompt, max_tokens, temperature, json_mode, timeout)
        if chosen_provider == "gemini":
            return _call_gemini(client, prompt, max_tokens, temperature, json_mode, timeout)

        # auto: Groq → Gemini 폴백.
        # Groq 가 더 빠르고 한도도 큼 → 우선. 실패 시 Gemini 로 다시 시도.
        result = _call_groq(client, prompt, max_tokens, temperature, json_mode, timeout)
        if result is not None:
            return result
        print("[llm_complete] groq 실패/미사용 → gemini 폴백 시도")
        return _call_gemini(client, prompt, max_tokens, temperature, json_mode, timeout)
    finally:
        if _owns_client:
            client.close()


def is_any_provider_configured() -> bool:
    """env 에 Groq 또는 Gemini key 가 설정됐는지 확인.

    챗봇 시작 시 사전 검증용. 둘 다 없으면 친절한 안내 메시지 띄움.
    """
    return bool(GROQ_API_KEY or GEMINI_API_KEY)


if __name__ == "__main__":
    # 모듈 단독 실행: 환경 검증 + 간단한 ping.
    print()
    if not is_any_provider_configured():
        print("❌ GROQ_API_KEY / GEMINI_API_KEY 둘 다 미설정. .env.example 참고.")
        exit(1)

    print("🧪 ping test...")
    resp = llm_complete("한 단어로 인사해줘", max_tokens=20)
    if resp:
        print(f"✓ 응답: {resp!r}")
    else:
        print("❌ 모든 provider 실패. API key / 네트워크 확인.")
