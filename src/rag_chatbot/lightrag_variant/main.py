"""
File: src/rag_chatbot/lightrag_variant/main.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
무엇 (What) — LightRAG 변형 K-Beauty 추천 챗봇의 Gradio entry point.
            provider 별 (groq / gemini) 인덱스 활용.
왜 (Why)    — GraphRAG 의 OpenAI 비용 / Ollama 호환성 문제 회피.
            E0 smoke test 통과 + E1 design 후 본격 챗봇.
어디 (Where) — 사용자가 `python -m src.rag_chatbot.lightrag_variant.main` 실행
어떻게 (How)

    # Groq (권장 — 무료 + 빠름)
    python -m src.rag_chatbot.lightrag_variant.main --provider groq

    # Gemini (fallback)
    python -m src.rag_chatbot.lightrag_variant.main --provider gemini

사전 조건:
1. `pip install -e ".[lightrag]"` (별도 venv 권장 — docs/setup_lightrag_env.md)
2. .env 에 GROQ_API_KEY 또는 GEMINI_API_KEY
3. 인덱싱 완료 — `python -m src.rag_chatbot.lightrag_variant.index_kbeauty
   --provider <provider>` (1회)

성공 시 콘솔에 `Running on local URL: http://127.0.0.1:7860` → 브라우저 자동 open.

자세히: src/rag_chatbot/lightrag_variant/README.md
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# REPO_ROOT 기반 portable import
_HERE = Path(__file__).resolve()
REPO_ROOT = next(p for p in _HERE.parents if (p / ".git").is_dir())
sys.path.insert(0, str(REPO_ROOT / "src"))

import gradio as gr  # noqa: E402

from rag_chatbot.lightrag_variant.builder import (  # noqa: E402
    build_lightrag, query_lightrag, working_dir_for,
)


def _check_indexing(provider: str) -> None:
    """인덱싱 완료 여부 사전 검증 — 부재 시 친절한 에러로 raise.

    Args:
        provider: ``"groq"`` / ``"gemini"``.
    """
    wdir = working_dir_for(provider)
    # graphml 파일이 LightRAG entity graph 의 핵심 산출물.
    if not (wdir / "graph_chunk_entity_relation.graphml").exists():
        raise FileNotFoundError(
            f"\n\n❌ LightRAG 인덱스 없음: {wdir}\n\n"
            f"먼저 인덱싱 실행:\n"
            f"   python -m src.rag_chatbot.lightrag_variant.index_kbeauty "
            f"--provider {provider}\n\n"
            f"자세히: src/rag_chatbot/lightrag_variant/README.md\n"
        )


def build_gradio(provider: str) -> gr.Blocks:
    """Gradio Blocks UI 구성 — provider 별 LightRAG 인스턴스 lazy 빌드.

    Args:
        provider: LightRAG variant ("groq" / "gemini").

    Returns:
        Gradio Blocks (실행: ``.launch()``).

    Note:
        LightRAG 인스턴스는 첫 query 시 *lazy* 생성 + 모듈-level 캐싱. 매 query
        마다 storage 재로드 안 함.
    """
    # 모듈 level singleton — Gradio multi-thread 환경에서도 한 번만 빌드.
    _rag_cache: dict = {}

    async def _get_rag():
        if "rag" not in _rag_cache:
            _rag_cache["rag"] = await build_lightrag(provider)
        return _rag_cache["rag"]

    def gradio_query(question: str, mode: str) -> str:
        if not question.strip():
            return "[안내] 질문을 입력하세요."
        try:
            async def _run():
                rag = await _get_rag()
                return await query_lightrag(rag, question, mode=mode)
            return asyncio.run(_run())
        except Exception as e:
            return f"[ERROR] {type(e).__name__}: {e}"

    with gr.Blocks() as demo:
        gr.Markdown(f"# K-Beauty 추천 챗봇 — LightRAG ({provider})")
        gr.Markdown(
            f"**Provider**: `{provider}` | **인덱스**: `{working_dir_for(provider)}`\n"
            "민감 피부 / 알러지 / 보습 등 자연어 조건으로 K-Beauty 5 브랜드 제품 추천."
        )
        with gr.Row():
            question_input = gr.Textbox(
                label="질문",
                placeholder="예: 건성 피부에 맞는 보습 크림 추천해줘",
                lines=2,
            )
            mode_input = gr.Dropdown(
                label="Query mode",
                choices=["naive", "local", "global", "hybrid"],
                value="hybrid",
                info="naive=가장 빠름 / hybrid=가장 정확 (E1 design 권장)",
            )
        query_btn = gr.Button("검색 실행", variant="primary")
        result_output = gr.Textbox(
            label="응답",
            placeholder="여기에 결과가 표시됩니다.",
            lines=10,
            interactive=False,
        )
        query_btn.click(
            fn=gradio_query,
            inputs=[question_input, mode_input],
            outputs=result_output,
        )

    return demo


def main() -> int:
    parser = argparse.ArgumentParser(description="LightRAG 변형 K-Beauty 챗봇")
    parser.add_argument(
        "--provider",
        choices=["groq", "gemini"],
        default="groq",
        help="LLM provider — groq (권장) / gemini (fallback)",
    )
    parser.add_argument(
        "--port", type=int, default=7860,
        help="Gradio port (default 7860). 다른 변형과 동시 실행 시 변경.",
    )
    args = parser.parse_args()

    # 인덱싱 사전 검증.
    try:
        _check_indexing(args.provider)
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        return 1

    demo = build_gradio(args.provider)
    demo.launch(server_port=args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
