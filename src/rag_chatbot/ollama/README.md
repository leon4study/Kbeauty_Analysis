# Ollama 기반 K-Beauty 추천 챗봇

K-Beauty 5 브랜드 (COSRX · PURITO · Beauty of Joseon · I'm From · Dr.Jart+) 의 제품·성분·효과 정보를 GraphRAG 로 인덱싱한 지식 그래프 위에서, 자연어로 화장품을 추천받는 챗봇입니다. 로컬 Ollama 사용으로 LLM 비용 0 + 프라이버시 이점.

> 같은 데이터로 OpenAI 변형 [`../cosmetic_rag_chat/`](../cosmetic_rag_chat/) 도 있습니다 (정확도 보강용).

## 사용 시나리오 예시

- *"민감 피부에 맞는 보습 크림 추천해줘"*
- *"파라벤 알러지 있는데 안전한 제품?"*
- *"건성 피부 + 알코올 free 클렌저"*

---

## 빠른 실행 (6 단계)

```bash
# 1. Python 의존성 설치 (uv 권장)
uv sync
# pip 사용 시: pip install -e .

# 2. Ollama 설치 (https://ollama.com) + 모델 다운로드
ollama pull gemma2              # LLM, 약 5GB
ollama pull nomic-embed-text    # 임베딩, 약 280MB

# 3. Ollama 데몬 시작 (이미 떠있으면 skip)
ollama serve

# 4. .env 셋업 (.env.example 의 Ollama default 가 이미 권장값)
cp .env.example .env

# 5. 인덱싱 input 준비 + GraphRAG 인덱싱 (~수 시간, 한 번만)
mkdir -p data/model/graphrag_t_2/input
cp examples/graphrag_input/5brand_graphrag_part.txt data/model/graphrag_t_2/input/
graphrag index --root ./data/model/graphrag_t_2

# 6. 챗봇 실행
python -m src.rag_chatbot.ollama.gradio_rag_ch7
```

→ 콘솔에 `Running on local URL: http://127.0.0.1:7860` 가 뜨면 브라우저 자동 열림. 채팅 박스에 자연어 질문 입력.

---

## 사전 준비

### 1. Python 환경 — uv 권장

uv 가 pip 대비 10~100배 빠르고 `uv.lock` 으로 환경 재현 보장.

```bash
# uv 설치 (없으면)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 의존성 설치
uv sync
```

**pip 대안**:

```bash
pip install -e .
```

### 2. Ollama (로컬 LLM)

```bash
# 1. https://ollama.com 에서 OS 별 설치
# 2. 모델 다운로드
ollama pull gemma2              # LLM, 약 5GB
ollama pull nomic-embed-text    # 임베딩, 약 280MB

# 3. 데몬 시작 (이미 떠있는지 확인)
ollama serve
# macOS 는 보통 메뉴바 아이콘에서 자동 시작
```

**확인**: `curl http://localhost:11434/api/tags` 가 응답하면 OK.

### 3. GraphRAG 인덱싱

K-Beauty 5 브랜드 제품·성분·효과 데이터를 GraphRAG 로 인덱싱한 결과 (LanceDB) 가 챗봇 응답의 근거.

**입력 데이터**: `examples/graphrag_input/5brand_graphrag_part.txt` (git 포함, 100K).
인덱싱 전에 `data/model/graphrag_t_2/input/` 으로 복사:

```bash
mkdir -p data/model/graphrag_t_2/input
cp examples/graphrag_input/5brand_graphrag_part.txt data/model/graphrag_t_2/input/
```

**인덱싱 실행**:

```bash
graphrag index --root ./data/model/graphrag_t_2
```

소요 시간:
- Ollama gemma2 (로컬): **수 시간** (CPU 기준, GPU 가속 시 단축)
- OpenAI API 사용 시: **수 분 ~ 수십 분** (API 비용 발생)

설정 변경: `data/model/graphrag_t_2/settings.yaml` (현재 Ollama gemma2 기본)

**결과**: `data/model/graphrag_t_2/output/lancedb/` 폴더 생성되면 인덱싱 완료.

> ⚠️ lancedb 폴더는 `.gitignore` 로 제외 — 처음 clone 한 사용자는 직접 인덱싱 필요.

### 4. 환경변수 (.env)

```bash
cp .env.example .env
```

`.env.example` 의 default 가 이미 Ollama 권장값 (`gemma2` + `nomic-embed-text` + `dummy` API key) — 그대로 cp 만 해도 동작.

자세한 prefix 규칙 + OpenAI 변형 전환 방법: [`.env.example`](../../../.env.example)

---

## 실행

```bash
python -m src.rag_chatbot.ollama.gradio_rag_ch7
```

성공 시 콘솔 출력:

```
Running on local URL: http://127.0.0.1:7860
```

브라우저가 자동으로 열리며 Gradio UI 등장. 채팅 박스에 자연어 질문 입력 (위 *사용 시나리오* 참고).

---

## 트러블슈팅

| 에러 | 원인 + 해결 |
| --- | --- |
| `FileNotFoundError: ... lancedb` | GraphRAG 인덱싱 안 됨 → *사전 준비 3. GraphRAG 인덱싱* 실행 |
| `ConnectionError: ... 11434` | Ollama 데몬 안 떠있음 → `ollama serve` 또는 `curl http://localhost:11434/api/tags` 응답 확인 |
| `ModuleNotFoundError: llama_index ...` | 의존성 미설치 → `uv sync` 또는 `pip install -e .` |
| `Out of memory` / 응답 느림 | gemma2 가 메모리 ~5GB+ 사용 → 작은 모델: `ollama pull gemma2:2b` 후 `gradio_rag_ch7.py` 의 `model="gemma2"` → `model="gemma2:2b"` 변경 |
| 첫 실행 시 sentence-transformers 다운로드 느림 | HuggingFace 임베딩 모델 (`all-mpnet-base-v2`) 첫 실행 시 자동 다운로드 (~수백 MB) — 캐시 후 빠름 |

---

## 파일 구성

| 파일 | 역할 |
| --- | --- |
| `gradio_rag_ch7.py` | **메인 챗봇** (실행 entry point) |
| `_experimental/OllamaLLM.py` | (미완성) LlamaIndex 용 Custom Ollama LLM wrapper (httpx 직접 사용) — 누락 import 3 개 + callers 0. 자세히 [`_experimental/README.md`](_experimental/README.md) |
| `check_db.ipynb` | LanceDB 검증 도구 (테이블 / entity 미리보기, 디버깅용) |
| `gradio_rag_ch8.ipynb` | LanceDB graph 데이터 깊이 활용 실험 (별도 진화 가지) |

---

## 개발 노트 (Development Notes)

`ch1 → ch7` progressive iteration 의 변종 카탈로그 + 진화 흐름 + 학습 포인트는 별도 docs 로 정리:

→ [`../../../docs/refactor/09_ollama_rag_variants.md`](../../../docs/refactor/09_ollama_rag_variants.md)

폐기된 변종 (`ch1`~`ch6`, `ch3` LangChain, `OllamaLLM v1` 등) 의 *왜 폐기했나* + git 복원 명령어도 거기 정리됨.

## 관련 docs

- [`../cosmetic_rag_chat/README.md`](../cosmetic_rag_chat/README.md) — OpenAI 변형 챗봇 (정확도 보강용)
- [`../../../docs/refactor/EXPERIMENTS_PLAYBOOK.md`](../../../docs/refactor/EXPERIMENTS_PLAYBOOK.md) — 변종 정리 표준
