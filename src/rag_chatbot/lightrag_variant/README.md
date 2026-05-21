# LightRAG 변형 (실험) — K-Beauty 챗봇

GraphRAG 대안으로 *시도해본* LightRAG 변형. 무료 LLM (Groq / Gemini) 위에서
인덱싱 + query 가능한지 검증한 결과물.

> **메인 챗봇은 여전히 GraphRAG 변형** ([`../cosmetic_rag_chat/`](../cosmetic_rag_chat/)).
> 본 LightRAG 변형은 *비교 / 실험 목적* 으로 추가됨.
> 평가 결과 (`docs/rag_evaluation_results.md`) 보고 메인 채택 여부 결정 예정.
>
> 배경 + design: [`../../../docs/lightrag_comparison_design.md`](../../../docs/lightrag_comparison_design.md)

## 빠른 실행 (5 단계, Groq 권장)

```bash
# 1. 별도 venv (필수 — graphrag 와 numpy 충돌 회피)
python3 -m venv ~/.venvs/kbeauty-lightrag
source ~/.venvs/kbeauty-lightrag/bin/activate
pip install -e ".[lightrag]"

# 2. Ollama 데몬 + bge-m3 embedding (Groq 가 chat 만 제공 → embedding 은 로컬)
ollama serve   # 별도 터미널 또는 이미 떠있으면 skip
ollama pull bge-m3            # embedding (~1.2GB, 1024 dim)

# 3. .env 셋업 — provider 별 API key
cp .env.example .env
# Groq: GROQ_API_KEY=gsk_... (https://console.groq.com 무료 발급)
# Gemini: GEMINI_API_KEY=AIza... (https://aistudio.google.com 무료 발급)

# 4. 인덱싱 (1회, ~10분 Groq 기준)
python -m src.rag_chatbot.lightrag_variant.index_kbeauty --provider groq

# 5. 챗봇 실행
python -m src.rag_chatbot.lightrag_variant.main --provider groq
```

→ 콘솔 `Running on local URL: http://127.0.0.1:7860` → 브라우저 자동 열림.

## 사용 시나리오

- *"민감 피부에 맞는 보습 크림 추천해줘"*
- *"파라벤 알러지 있는데 안전한 클렌저"*
- *"건성 피부 + 알코올 free 클렌저"*

## Provider

| Provider | 인덱싱 시간 (100KB) | 비용 | 위치 |
|---|---|---|---|
| **`groq`** | **~10분** | **0** | 메인 권장 (Llama 3.3 70B) |
| `gemini` | ~30분 | 0 | fallback (Flash Lite) |

자세한 estimate: [`../../../docs/lightrag_comparison_design.md`](../../../docs/lightrag_comparison_design.md) §3.

> Ollama 변형은 E0 smoke test 에서 *동작은 검증* 했지만 100KB 인덱싱이
> ~7시간 추정 → 실용성 X. 본 챗봇 에서는 미지원.

## Query mode

LightRAG 의 4 모드 (Gradio dropdown 에서 선택):

| Mode | 동작 | 속도 | 정확도 |
|---|---|---|---|
| `naive` | embedding 만 (entity graph 우회) | 빠름 | 낮음 |
| `local` | entity neighbor 위주 | 중간 | 중간 |
| `global` | community 위주 | 느림 | 중간 |
| `hybrid` | local + global 결합 | 가장 느림 | **가장 높음 — default** |

## 디렉토리 구조

```
lightrag_variant/
├── __init__.py
├── builder.py            # build_lightrag / query_lightrag (provider 별 통합 빌더)
├── index_kbeauty.py      # 인덱싱 CLI (1회 실행)
├── main.py               # Gradio 챗봇 entry
├── README.md             # 이 파일
└── indexing/             # (생성됨) provider 별 storage 는 data/model/lightrag_<provider>/
```

## 사전 조건 상세

### 1. Python 환경 — 별도 venv 필수

graphrag 0.3.0 (numpy<2) vs lightrag-hku (numpy 2.x) 충돌. 자세히:
[`../../../docs/setup_lightrag_env.md`](../../../docs/setup_lightrag_env.md)

### 2. Ollama 데몬 (embedding bge-m3 용)

bge-m3 가 모든 provider 의 embedding (Groq/Gemini 변형도 — Groq 는 embedding
미지원, Gemini 는 옵션). Ollama 데몬 떠있고 `bge-m3` 모델 다운로드 필수.

```bash
ollama serve
ollama pull bge-m3
```

확인: `curl http://localhost:11434/api/tags` 응답.

### 3. API Key (provider 별)

- **Groq**: https://console.groq.com 무료 가입, `GROQ_API_KEY=gsk_...`
- **Gemini**: https://aistudio.google.com 무료 발급, `GEMINI_API_KEY=AIza...`

`.env.example` 참고.

## 트러블슈팅

| 에러 | 원인 + 해결 |
| --- | --- |
| `❌ LightRAG 인덱스 없음: ...` | 인덱싱 안 함 → `python -m src.rag_chatbot.lightrag_variant.index_kbeauty --provider <provider>` |
| `ImportError: lightrag-hku 미설치` | venv 활성화 안 됨 또는 `pip install -e ".[lightrag]"` 안 함 |
| `EnvironmentError: GROQ_API_KEY 미설정` | `.env` 에 key 추가 후 셸 재시작 |
| `ConnectionError: ... 11434` | Ollama 데몬 안 떠있음 → `ollama serve` |
| `ValueError: query vector dimension mismatch` | 인덱싱과 다른 embedding 모델로 query → 같은 provider 의 인덱스 사용 |
| 인덱싱 너무 느림 (Ollama) | Groq 로 전환 권장 (`--provider groq`) |

## 평가 (vs GraphRAG)

평가 framework + golden 10 질문 으로 비교:

```bash
# LightRAG 변형 평가
python -m tests.rag_eval.evaluate --provider lightrag-groq

# 비교 (GraphRAG 변형도 같이)
python -m tests.rag_eval.evaluate --provider groq    # GraphRAG + Groq
python -m tests.rag_eval.evaluate --provider lightrag-groq   # LightRAG + Groq
```

결과: `tests/rag_eval/results/lightrag-<provider>_<date>.json`. 종합 표는
`docs/rag_evaluation_results.md` (PR-D 후속).

자세한 metric: [`../../../docs/rag_evaluation_framework.md`](../../../docs/rag_evaluation_framework.md)

## 관련 docs

- [`../../../docs/lightrag_comparison_design.md`](../../../docs/lightrag_comparison_design.md)
  — E1 design (이 변형의 청사진)
- [`../../../docs/setup_lightrag_env.md`](../../../docs/setup_lightrag_env.md)
  — venv 분리 가이드
- [`../../../examples/lightrag_smoke_test/`](../../../examples/lightrag_smoke_test/)
  — E0 검증 결과
- [`../cosmetic_rag_chat/README.md`](../cosmetic_rag_chat/README.md) — GraphRAG OpenAI 변형
- [`../ollama/README.md`](../ollama/README.md) — GraphRAG Ollama 변형 (실험)
