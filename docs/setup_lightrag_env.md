# [←](../README.md) LightRAG 변형 — 별도 venv 셋업 가이드

`src/rag_chatbot/lightrag_variant/` 사용 시 *별도 venv* 권장. 이유:
LightRAG (`lightrag-hku`) 가 `numpy 2.x` 의존인데 기존 `graphrag 0.3.0` 은
`numpy<2.0` 요구 → 같은 venv 에 두면 한쪽 깨짐.

## 왜 venv 분리

E0 smoke test 설치 시 발견된 충돌:

```
graphrag 0.3.0      requires numpy<2.0.0    but you have numpy 2.2.6
gradio 5.14.0       requires aiofiles<24    but you have aiofiles 24.1.0
graspologic 3.4.1   requires numpy<2.0.0    (graphrag transitive)
llama-index-core    requires nltk>3.8.1     but 3.8.1
```

→ **graphrag 변형이 numpy 2.x 에서 동작 불안정**. 운영 옵션 3 가지:

| 옵션 | 장점 | 단점 |
|---|---|---|
| **A: 별도 venv** (이 문서) | 두 변형 모두 안정 동작 | venv 2개 관리 |
| B: graphrag 폐기 (LightRAG 만) | venv 1개 | 비교 안 됨, 옛 챗봇 못 씀 |
| C: numpy<2.0 강제 + lightrag 강제 설치 | venv 1개 | 어느 하나 깨질 위험 |

→ **A 권장**. 비교 결과 후 (E3 단계) C 검토 가능.

## 셋업

### 1. 새 venv 생성

```bash
python3 -m venv ~/.venvs/kbeauty-lightrag
source ~/.venvs/kbeauty-lightrag/bin/activate

# 확인 — venv 안인지
which python   # → ~/.venvs/kbeauty-lightrag/bin/python
```

### 2. LightRAG 변형 의존성만 설치

```bash
cd /path/to/Kbeauty_Analysis
pip install -e ".[lightrag]"
```

→ `pyproject.toml` 의 `[lightrag]` extras 만 설치 (graphrag/lancedb 제외).

### 3. Ollama 모델 다운로드 (LightRAG-Ollama 변형 사용 시)

```bash
ollama serve   # 이미 떠있으면 skip
ollama pull gemma2          # LLM (~5GB)
ollama pull bge-m3          # embedding (~1.2GB)
# 더 큰 LLM (정확도 ↑): ollama pull qwen2.5:7b
```

### 4. ping 확인

```bash
python examples/lightrag_smoke_test/smoke_test.py
```

E0 smoke test 통과해야 본격 사용 가능.

## 두 venv 전환 사용

```bash
# graphrag 변형 사용
source ~/.venvs/kbeauty-graphrag/bin/activate
python -m src.rag_chatbot.cosmetic_rag_chat.main

# LightRAG 변형 사용
source ~/.venvs/kbeauty-lightrag/bin/activate
python -m src.rag_chatbot.lightrag_variant.main
```

평가 (`tests/rag_eval/evaluate.py`) 도 *각자 변형의 venv 에서* 실행:

```bash
# graphrag 변형 평가
source ~/.venvs/kbeauty-graphrag/bin/activate
python -m tests.rag_eval.evaluate --provider groq

# LightRAG 변형 평가
source ~/.venvs/kbeauty-lightrag/bin/activate
python -m tests.rag_eval.evaluate --provider lightrag-groq
```

## 환경변수 (`.env`)

`.env` 는 *공유* — 양 venv 모두 같은 key 사용:

```bash
GROQ_API_KEY=gsk_...
GEMINI_API_KEY=AIza...
GRAPHRAG_API_KEY=...    # graphrag 변형 인덱싱용
```

## 트러블슈팅

### `ModuleNotFoundError: lightrag`
→ venv activate 안 됨 또는 `pip install -e ".[lightrag]"` 안 함.

### `numpy version conflict`
→ graphrag 변형 venv 와 섞임. `pip list | grep numpy` 로 2.x 확인.

### 인덱싱 (E2-4) 너무 느림
→ Ollama 로컬 모델 사용 시 *수 시간* 예상. Groq (`--provider lightrag-groq`) 추천 — 무료 한도 안에서 ~10분.

### Ollama 데몬 안 떠있음
→ `ollama serve` 실행 후 `curl localhost:11434/api/tags` 응답 확인.

## 관련

- [`lightrag_comparison_design.md`](lightrag_comparison_design.md) — E1 design (이 venv 설정 결정 근거)
- [`../examples/lightrag_smoke_test/`](../examples/lightrag_smoke_test/) — E0 검증 결과
- [`../src/rag_chatbot/lightrag_variant/`](../src/rag_chatbot/lightrag_variant/) — LightRAG 챗봇 (E2)
