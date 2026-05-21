"""LightRAG 기반 K-Beauty 챗봇 변형 (E2 — Plan E 구현).

provider 별 LightRAG 인스턴스:
- groq: Groq Llama 3.3 70B + 로컬 Ollama embedding (메인 권장)
- gemini: Gemini Flash + Gemini embedding (fallback)

자세히: docs/lightrag_comparison_design.md
"""
