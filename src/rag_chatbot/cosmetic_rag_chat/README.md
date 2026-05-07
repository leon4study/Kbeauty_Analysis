# OpenAI 기반 K-Beauty 추천 챗봇

K-Beauty 5 브랜드 (COSRX · PURITO · Beauty of Joseon · I'm From · Dr.Jart+) 의 제품·성분·효과 정보를 GraphRAG 로 인덱싱한 지식 그래프 위에서, 자연어로 화장품을 추천받는 챗봇입니다. **OpenAI gpt-3.5-turbo + text-embedding-3-small** 사용 (정확도 보강용).

> 같은 데이터로 로컬 Ollama 변형 [`../ollama/`](../ollama/) 도 있습니다 (비용·프라이버시 이점).

## 사용 시나리오 예시

- *"민감 피부에 맞는 보습 크림 추천해줘"*
- *"파라벤 알러지 있는데 안전한 제품?"*
- *"건성 피부 + 알코올 free 클렌저"*

---

## 빠른 실행 (4 단계)

```bash
# 1. Python 의존성 설치
uv sync   # 또는: pip install -e .

# 2. .env 셋업 — OpenAI API key 필요
cp .env.example .env   # GRAPHRAG_API_KEY 에 실제 OpenAI key 채우기

# 3. GraphRAG 인덱싱 (~수 분 ~ 수십 분, OpenAI API 비용 발생)
graphrag index --root ./src/rag_chatbot/cosmetic_rag_chat/indexing

# 4. 챗봇 실행
python -m src.rag_chatbot.cosmetic_rag_chat.main --method local
```

→ 콘솔에 `Running on local URL: http://127.0.0.1:7860` 가 뜨면 브라우저 자동 열림.

---

## 사전 준비

### 1. Python 환경

```bash
# uv 권장 (10~100배 빠름)
uv sync

# pip 대안
pip install -e .
```

### 2. OpenAI API Key

OpenAI 계정 + API key 필요 — https://platform.openai.com/api-keys 에서 발급.

비용 가이드 (대략):
- **인덱싱** (한 번만, 5,000 영상 데이터): 약 $5~10
- **챗봇 응답** (질문 1개당): 약 $0.001~0.005

### 3. 환경변수 (.env)

```bash
cp .env.example .env
```

필수 변수 (OpenAI 사용 시):
- `GRAPHRAG_API_KEY=sk-...` (OpenAI key)
- `LLM_MODEL=gpt-3.5-turbo`
- `EMBED_MODEL=text-embedding-3-small`
- `LLM_API_BASE=https://api.openai.com/v1`

자세한 prefix 규칙: [`.env.example`](../../../.env.example)

### 4. GraphRAG 인덱싱

K-Beauty 5 브랜드 데이터를 GraphRAG 로 인덱싱한 결과 (LanceDB) 가 챗봇 응답의 근거.

**입력 데이터**: `data/model/graphrag_t_2/input/5brand_graphrag_part.txt` (git 에 포함, ollama 변형과 공유)

**설정 파일**: `indexing/settings.yaml` (OpenAI gpt-3.5-turbo 기본)

**인덱싱 실행**:

```bash
graphrag index --root ./src/rag_chatbot/cosmetic_rag_chat/indexing
```

소요 시간:
- OpenAI API 사용 시: **수 분 ~ 수십 분**
- 비용: ~$5~10 (한 번만)

**결과 위치**: `indexing/output/lancedb/` 또는 `cosmetic_rag_chat/lancedb/` (settings.yaml 의 output_dir 설정 따라)

> ⚠️ lancedb 폴더는 `.gitignore` 로 제외 — 처음 clone 한 사용자는 직접 인덱싱 필요.

---

## 실행

### Local Search (기본)

지역적 검색 — 특정 entity 와 그 이웃 노드 위주.

```bash
python -m src.rag_chatbot.cosmetic_rag_chat.main --method local
```

### Global Search

전역 검색 — 전체 그래프 community summary 활용.

```bash
python -m src.rag_chatbot.cosmetic_rag_chat.main --method global
```

성공 시:
- 콘솔에 `Running on local URL: http://127.0.0.1:7860`
- 브라우저 자동 열림
- 텍스트 박스에 자연어 질문 → *검색 실행* 버튼

---

## 트러블슈팅

| 에러 | 원인 + 해결 |
| --- | --- |
| `WARNING: settings.yaml 파일이 비어 있거나, 올바르게 로드되지 않았습니다` | `indexing/settings.yaml` 경로 확인 또는 `.env` 의 `GRAPHRAG_CONFIG` 값 확인 |
| `openai.AuthenticationError` | `.env` 의 `GRAPHRAG_API_KEY` 가 잘못됨 → OpenAI 대시보드에서 key 재발급 |
| `FileNotFoundError: ... lancedb` | GraphRAG 인덱싱 안 됨 → *사전 준비 4* 실행 |
| `ModuleNotFoundError: graphrag` | 의존성 미설치 → `uv sync` 또는 `pip install -e .` |
| `RateLimitError` (OpenAI) | API quota 초과 → 결제 정보 확인 또는 `tokens_per_minute` 낮춤 (settings.yaml) |

---

## 파일 구성

| 파일 | 역할 |
| --- | --- |
| `main.py` | **메인 챗봇** (실행 entry point, argparse `--method local/global`) |
| `final_graphrag_LLM.py` | 챗봇 + 그래프 시각화 (디버깅·시연용 alternative entry) |
| `indexing/settings.yaml` | GraphRAG 인덱싱 설정 (OpenAI gpt-3.5-turbo + text-embedding-3-small) |
| `indexing/.env` | (선택) 인덱싱 전용 환경변수 (없으면 프로젝트 root `.env` fallback) |

---

## 관련 docs

- [`../ollama/README.md`](../ollama/README.md) — Ollama 로컬 변형 (비용 0)
- [`../../../docs/refactor/EXPERIMENTS_PLAYBOOK.md`](../../../docs/refactor/EXPERIMENTS_PLAYBOOK.md) — 변종 정리 표준
