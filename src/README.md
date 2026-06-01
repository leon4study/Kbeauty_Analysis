# `src/` — 코드 모듈 카탈로그

K-Beauty 분석 프로젝트의 코드 구성. 5 module.

| Module | 역할 | 메인 파일 |
| --- | --- | --- |
| [amazon_review_crawler/](#amazon_review_crawler) | Amazon 리뷰 수집 | `main.py` |
| [tiktok_crawler/](#tiktok_crawler) | TikTok 영상 수집 (반자동) | `tiktok_crawling.py` |
| [pipelines/](#pipelines) | medallion 변환 파이프라인 (bronze → silver) | `build_silver_amazon.py`, `build_silver_tiktok.py` |
| [rag_chatbot/](#rag_chatbot) | 개인 맞춤 화장품 추천 챗봇 (메인: `cosmetic_rag_chat/`, 실험: `lightrag_variant/`, archived: `_experimental/ollama/`) | `cosmetic_rag_chat/main.py` |
| [util/](#util) | 공통 유틸리티 | `repo_paths.py`, `negation.py` 등 |

---

## amazon_review_crawler/

Amazon 미국 사이트에서 K-Beauty 5 브랜드 (COSRX · PURITO · Beauty of Joseon · I'm From · Dr.Jart+) 의 제품 정보와 고객 리뷰를 크롤링해 MySQL 에 적재하는 모듈입니다.

**왜 Selenium 인가**:
Amazon 공식 API 가 리뷰 본문 접근을 막아 두었기 때문에, 브라우저 자동화 (Selenium WebDriver) 로 우회합니다. 로그인 → 검색 → 페이지네이션 → HTML 파싱 전 과정을 자동화했고, 다중 계정 rotation 도 지원합니다.

**구성**:
- `main.py` — 메인 크롤러 (40KB). Selenium WebDriver + 로그인 → 검색 → 리뷰 파싱 메인 루프
- `mysql.py` — MySQL connector 래퍼 + SQLAlchemy ORM 스키마
- `reviews.py`, `items.py` — DataFrame → MySQL 적재 함수 + 스키마 검증

**사용 방법**:
```bash
python -m src.amazon_review_crawler.main
```

**출력물**:
```
data/bronze/amazon/{brand}_items.csv      ← 제품 정보 (이름·가격·평점 등)
data/bronze/amazon/{brand}_reviews.csv    ← 리뷰 본문 (별점·날짜·sentiment 등)
```

**의존성**: Selenium · SQLAlchemy · MySQL 서버 · `.env` (Amazon 계정 + Slack webhook URL)

---

## tiktok_crawler/

TikTok 검색 결과에서 영상 메타데이터 (조회수 · 좋아요 · 댓글 · 저장 · 설명 · 업로드일 · 인플루언서명) 를 수집하는 모듈입니다.

**왜 반자동 인가**:
TikTok 은 공식 API 인증이 까다롭고 인플루언서 단위 데이터 접근에 제한이 강합니다. 또 CAPTCHA 인증 창이 자주 떠서 완전 자동화가 불가능 — 인증 단계는 사람이 통과하고 나머지는 자동으로 진행하는 반자동 구조입니다.

**구성**:
- `tiktok_crawling.py` — 키워드별 검색 (`clean_beauty`, `glow_skin`, `kbeauty_skin_care`, `korean_skincare`) → 50~200 영상 메타데이터 파싱

**사용 방법**:
```bash
python -m src.tiktok_crawler.tiktok_crawling
```
실행 중 CAPTCHA 인증 창이 뜨면 사람이 직접 통과 → 이후 자동 수집 재개.

**출력물**:
```
data/bronze/tiktok/tiktok_search_<keyword>[_v<n>][_<date>].csv  ← 키워드 검색 결과
data/bronze/tiktok/tiktokers_raw.csv                            ← 인플루언서별 raw 데이터
```

**의존성**: Selenium · `.env` (TikTok 세션 자격증명)

---

## pipelines/

medallion 아키텍처의 bronze → silver 변환을 모듈화한 CLI 파이프라인.

| 파일 | 역할 |
| --- | --- |
| `build_silver_amazon.py` | bronze/amazon 5브랜드 items/reviews + skinsort → silver 3 파일 (lemmatize + n-gram + 번역) |
| `build_silver_tiktok.py` | bronze/tiktok 검색 CSV 들 → silver/tiktok/tiktok_videos_silver.csv (rename + dedup + hash_tag) |

**왜 노트북 안 두고 스크립트로 빼냈는가**:
- 노트북 run-all 시 silver 덮어쓰기 사이드이펙트 위험
- `--overwrite` 플래그 + 명시적 실행으로 의도치 않은 덮어쓰기 방지
- Python 모듈이라 단위 테스트 가능

**사용 방법**:
```bash
# 처음 생성
python src/pipelines/build_silver_tiktok.py
python src/pipelines/build_silver_amazon.py

# 덮어쓰기 (신규 raw 추가 후)
python src/pipelines/build_silver_amazon.py --overwrite --translate
python src/pipelines/build_silver_tiktok.py --overwrite
```

---

## rag_chatbot/

분석 결과를 활용한 **개인 맞춤 화장품 추천 챗봇** 모듈입니다. 고객이 자기 피부 타입, 알러지 성분, 원하는 효과를 자연어로 입력하면 graph 가 *제품 - 성분 - 효과 - 피부 타입* 관계를 따라 추천합니다.

**사용 시나리오**:
- *"건성 피부에 맞는 보습 크림 추천해줘"*
- *"알코올 성분 없는 클렌저 알려줘"*
- *"파라벤 알러지 있는데 안전한 제품?"*

**왜 GraphRAG 인가**:
단순 텍스트 RAG (벡터 검색 + LLM) 는 *"민감 피부 + 히알루론산 + 알코올 제외"* 같이 여러 조건이 얽힌 multi-hop 질의에 약합니다. Graph 노드 (제품 · 성분 · 효과 · 피부 타입) 사이의 관계를 직접 따라가면 다중 조건도 자연스럽게 처리됩니다.

**구조**:
- 약 570 개 entity 노드 — BRAND 5 + TYPE 46 + INGREDIENT 498 + EFFECT 23
- LanceDB 벡터 스토어 (노드 임베딩 검색)
- Microsoft GraphRAG 프레임워크

**메인 + 실험 변형**:

### `cosmetic_rag_chat/` — **메인** (GraphRAG + OpenAI gpt-3.5-turbo)

정확도 + 안정성. YAML config 기반 경로 portability.

- 메인: `main.py` — argparse 기반 (`--method local|global`)
- 자세히: [`cosmetic_rag_chat/README.md`](rag_chatbot/cosmetic_rag_chat/README.md)

```bash
python -m src.rag_chatbot.cosmetic_rag_chat.main --method local
```

### `lightrag_variant/` — 실험 (LightRAG + Groq/Gemini 무료)

GraphRAG 대안으로 *시도해본* LightRAG 변형. 평가 결과 (`docs/rag_evaluation_results.md`)
보고 메인 채택 여부 결정 예정. 자세히: [`lightrag_variant/README.md`](rag_chatbot/lightrag_variant/README.md)

### `_experimental/ollama/` — archived (옛 Ollama 변형)

GraphRAG + Ollama gemma2 시도 — 호환성 issue + 실용성 ↓ 로 `_experimental/` 격리.
*동작 검증 흔적* 으로 보존. 자세히: [`_experimental/ollama/README.md`](rag_chatbot/_experimental/ollama/README.md)
및 [`../docs/refactor/15_ollama_graphrag_compatibility.md`](../docs/refactor/15_ollama_graphrag_compatibility.md).

**의존성**: Microsoft GraphRAG · LanceDB · LlamaIndex · Gradio · OpenAI API key
(LightRAG 변형은 별도 venv + Groq/Gemini key)

---

## util/

전 모듈에서 공통으로 쓰는 유틸리티.

| 파일 | 역할 |
| --- | --- |
| `repo_paths.py` | `.git` 디렉토리 기준으로 저장소 root 자동 감지. 노트북 / 스크립트 어디서 실행해도 `BRONZE_AMAZON`, `SILVER_AMAZON`, `BRONZE_TIKTOK`, `SILVER_TIKTOK`, `GOLD_AMAZON`, `GOLD_TIKTOK` 절대경로 사용 가능. legacy `AMAZON`/`TIKTOK` 도 유지 (마이그레이션 진행 중) |
| `data_io.py` | 자주 쓰는 데이터 로드 함수 (`load_keyword_dfs()` 등) + `AMAZON_BRANDS` 5 브랜드 슬러그 상수 |
| `tiktok_metrics.py` | TikTok raw 데이터 벡터화 헬퍼 — `parse_metric_with_unit` (K/M/B 단위), `parse_relative_date` (mixed-format), `extract_hashtags_and_mentions`, `bucket_influencer_size` (mega/mekro/middle/micro/nano), `format_year_month`. 3 노트북에서 중복 정의됐던 함수들을 통합 + 벡터화 (50배+ 빠름) |
| `negation.py` | Amazon 리뷰의 *"not sticky"*, *"alcohol-free"*, *"non-comedogenic"* 같은 부정 표현을 NLP 정규화하는 4 단계 파이프라인 (NLTK + PMI bigram + 도메인 lexicon + SpaCy 의존구문분석) |
| `slack.py` | Slack incoming webhook 알림 (`send_msg(msg)`). 장시간 크롤러 / 배치 작업 완료 또는 에러 시 채널에 메시지 전송 |

**사용 예시**:
```python
from src.util.repo_paths import BRONZE_AMAZON, SILVER_AMAZON, BRONZE_TIKTOK
from src.util.data_io import load_keyword_dfs, AMAZON_BRANDS
from src.util.slack import send_msg

# medallion 경로 사용
import pandas as pd
df = pd.read_csv(BRONZE_AMAZON / "cosrx_reviews.csv")     # raw
df_silver = pd.read_csv(SILVER_AMAZON / "amazon_reviews_lemmatized.csv")  # 정제

# Slack 알림
send_msg("크롤러 완료: 약 2만 건 수집")
```

**의존성**: NLTK · spaCy · pandas · requests

---

## 의존성 설치

```bash
# editable install (pyproject.toml 기반)
pip install -e .
```

**주요 패키지**: pandas · numpy · scikit-learn · statsmodels · gensim · nltk · spaCy · Selenium · SQLAlchemy · graphrag · lancedb · llama-index · gradio · ollama
