# K-Beauty 미국 시장 분석 (Kbeauty_Analysis)

Amazon 경쟁사 리뷰와 TikTok 인플루언서 데이터를 통합 분석해 신규 인디 K-Beauty 브랜드의 미국 Amazon 시장 진출 전략을 데이터로 설계한 엔드투엔드 프로젝트.

가상 페르소나 *3-beaty* (히알루론산 기반 인디 K-Beauty, Torriden 을 reference) 의 진출을 두 갈래로 풀었습니다 — **Amazon 갈래**: 1.2만 리뷰 → Chi-square 가설 깨짐 (p > 0.9) → *제품 만족이 사용 경험·피부 타입에 의존* 인사이트 → TF-IDF / LDA → 3-beaty USP 도출 → GraphRAG 챗봇. **TikTok 갈래**: 4,600 영상 수집 → 1,680 영상 분석 → OLS → PSM → within-influencer FE → K-Premium 4.76 ~ 5.10 %p 정량화 → 그 효과의 95% 가 *인플루언서 selection effect* 임을 발견 → ver.1 → ver.4 추천 알고리즘 (1.25배 → 3.25배 random ER% 대비).

> 프로젝트 narrative 는 별도 노션 페이지로 정리. 본 README 는 코드베이스 navigation + 핵심 결과 요약.

---

## 1. `src/` — 코드 설명

각 module: 무엇 / 왜 / 사용 방법.

### 1-1. `src/amazon_review_crawler/`

**무엇**: Selenium 기반 Amazon 리뷰 크롤러 + MySQL 적재 (5 brand 1.2만 건).

**왜 Selenium**: Amazon 공식 API 가 review 본문 접근 X.

**구성**:
- `main.py` — WebDriver + 로그인 → 검색 → 리뷰 파싱 메인 루프 (`.env` 자격증명 + Slack 알림)
- `mysql.py` — MySqlConnector 래퍼, SQLAlchemy ORM 스키마
- `reviews.py`, `items.py` — DataFrame → MySQL 적재 함수

**사용**: `python -m src.amazon_review_crawler.main` → `data/amazon/{brand}_items.csv`, `{brand}_reviews.csv`

### 1-2. `src/tiktok_crawler/`

**무엇**: 반자동 TikTok 검색 결과 메타데이터 크롤러 (CAPTCHA 통과는 수동).

**왜 반자동**: TikTok 공식 API 인증 + 인플루언서 단위 데이터 접근 어려움.

**구성**:
- `tiktok_crawling.py` — 키워드 검색 → 50~200 영상 메타데이터 (view, like, comment, save, 설명, 업로드일, 인플루언서명) 파싱
- `tiktoker_crawling.ipynb` — 인플루언서 단위 메타데이터 수집 (진행형)

**사용**: `python -m src.tiktok_crawler.tiktok_crawling` → `data/tiktok/tiktok_post_final_df.csv`, `tiktoker_crawling_df_*.csv`

### 1-3. `src/rag_chatbot/`

GraphRAG (지식 그래프 + LLM) 기반 성분-효과 추천 챗봇. **두 변형 분리 실행 + 비교**:

#### `ollama/` — 로컬 LLM 변형 ([상세 README →](src/rag_chatbot/ollama/README.md))

**무엇**: Microsoft GraphRAG + LanceDB + Ollama (gemma2 + nomic-embed-text) + Gradio multimodal UI.

**왜 로컬**: 비용 절감 + 프라이버시.

**메인**: `gradio_rag_ch7.py` (ch1 → ch7 progressive 진화의 최종 단계). ch1 ~ ch6 은 git history 보존.

**사용**: `python -m src.rag_chatbot.ollama.gradio_rag_ch7` (Ollama 데몬 `localhost:11434` + 인덱스 `data/model/graphrag_t_2/output/lancedb` 필요)

#### `cosmetic_rag_chat/` — OpenAI 변형

**무엇**: GraphRAG + LanceDB + OpenAI (gpt-3.5-turbo + text-embedding-3-small) + YAML config 기반 경로 portability.

**메인**: `main.py` — argparse 기반 (`--search-type local|global`).

### 1-4. `src/util/` — 공통 유틸리티

| 파일 | 역할 |
| --- | --- |
| `repo_paths.py` | `.git` 기준 REPO_ROOT 자동 감지 → `AMAZON`, `TIKTOK`, `DATA`, `MODEL` 절대경로 상수. 노트북 어디서 실행해도 portable |
| `data_io.py` | 반복 로드 함수화 (`load_keyword_dfs()` 등). `AMAZON_BRANDS` 상수 |
| `negation.py` | Amazon 리뷰 부정어 처리 4 단계 파이프라인. (1) NLTK `mark_negation` (2) PMI bigram (3) 도메인 lexicon (4) SpaCy 의존구문분석. *"not sticky"*, *"non-comedogenic"* 같은 표현 NLP 정규화 |
| `slack.py` | Incoming webhook 알림 (`send_msg(msg)`). 장시간 크롤러 / 배치 작업 모니터링 |

---

## 2. `notebooks/` — 실험 + 결과

각 노트북: 실험 의도 + 핵심 결과. 디테일 카탈로그는 subdir README 참고.

### 2-1. Top-level

| 노트북 | 무엇 | 핵심 결과 |
| --- | --- | --- |
| `EDA.ipynb` | Amazon 5 brand 기본 EDA (brand · price · rating · sentiment · word cloud) | 브랜드별 리뷰 수 / sentiment 분포 / Skinsort 가격 통합 |
| `lemmatized_full_pipeline.ipynb` | Amazon 리뷰 통합 전처리 + LDA 토픽 모델링 (lemmatize → n-gram → Phrases → LDA) | 브랜드별 토픽 클러스터링 + 성분/기능 토픽 추출 |

### 2-2. `notebooks/tiktok/` — 영상·인플루언서 분석 (8 노트북)

상세 카탈로그 → [notebooks/tiktok/README.md](notebooks/tiktok/README.md)

| 노트북 | 무엇 | 핵심 결과 |
| --- | --- | --- |
| `tiktok_marketing_modeling_v2.ipynb` ⭐ **메인** | PSM (Propensity Score Matching) ATT 추정 | K-Premium ATT = **+4.76 %p** (p<0.05) |
| `tiktok_statistic_analysis.ipynb` | within-influencer Fixed Effect | K-Beauty 키워드 단독 효과 = **+0.24 %p (p=0.75)** → selection effect 95% 발견 |
| `tiktoker_recommend.ipynb` | 추천 알고리즘 ver.1 / v2 / v3 / v4 진화 | Top-10 무작위 대비 **3.25배 ER%**, Precision@10 = 60% |
| `tiktoker_topic_modeling.ipynb` | LDA → 인플루언서별 콘텐츠 토픽 (9 토픽) | color / skincare / hair_body / fashion / asmr / 등 |
| `tiktoker_labeling.ipynb` | 토픽 모델 결과 → 카테고리 라벨링 | `tiktoker_top3_modeled_topic.csv` |
| `tiktok_EDA.ipynb` | 영상 단위 기본 EDA | 키워드별 engagement 분포, k/m 단위 변환 |
| `tiktoker_EDA.ipynb` | 인플루언서 단위 EDA | follower / 영상 수 분포 |
| `experiments/tiktok_marketing_modeling_v1.ipynb` | v1 변종 (이전 refactor) | sklearn LogisticRegression PSM, 그룹 라벨 구식 |

### 2-3. `notebooks/amazon_tiktok/` — Amazon × TikTok 결합 분석 (7 노트북)

상세 카탈로그 → [notebooks/amazon_tiktok/README.md](notebooks/amazon_tiktok/README.md)

| 노트북 | 무엇 | 핵심 결과 |
| --- | --- | --- |
| `05_without_wonyoung_main.ipynb` ⭐ **메인** | 가설 정식 검증 (장원영 이상치 제외 + non_k_skincare 비교군 정밀화) | K-keyword vs non_k 비교 → OLS **+5%p K-Premium** |
| `05_without_wonyoung_presentation.ipynb` | 메인 정제본 (전처리 제거, 결과만) | 발표 / 리뷰용 |
| `experiments/01_baseline_colab_eda.ipynb` | Colab 기반 lemmatize + word counts | 558줄 |
| `experiments/02_added_ngram_pmi.ipynb` | + n-gram + PMI + spacy + negation 모듈 적용 예시 | [`src/util/negation.py`](src/util/negation.py) 선제 사례 |
| `experiments/03_added_statistical_test.ipynb` | + plotly + 회귀 / shapiro / levene / ttest | 697줄 |
| `experiments/04_kkeyword_revised_1228.ipynb` | k_keyword 재정의 (wonyoung 제거, korea 추가) | 701줄 |

**진화 흐름**: 01 baseline → 02 +n-gram → 03 +통계검정 → 04 k_keyword 재정의 → 05 main (정식)

---

## 3. 전체 파이프라인

```
┌─────────────────────────────────────────────────────────────────┐
│                      DATA SOURCES                                │
│ Amazon: 5 brands (Dr.Jart+ · COSRX · I'm From · Beauty of       │
│         Joseon · PURITO) — items + reviews                      │
│ TikTok: 4 검색어 (clean_beauty · glow_skin · kbeauty_skin_care  │
│         · korean_skincare) — 영상 메타데이터                     │
└─────────────────────────────────────────────────────────────────┘
        │                                         │
        ▼                                         ▼
  src/amazon_review_crawler/              src/tiktok_crawler/
  (Selenium + MySQL)                      (Selenium 반자동)
        │                                         │
        ▼                                         ▼
  data/amazon/                            data/tiktok/
  {brand}_items.csv                       tiktok_post_final_df.csv
  {brand}_reviews.csv                     tiktoker_crawling_df_*.csv
        │                                         │
        ▼                                         ▼
  notebooks/EDA.ipynb                     notebooks/tiktok/tiktok_EDA
  notebooks/lemmatized_full_pipeline      notebooks/tiktok/tiktoker_*
  (lemmatize + LDA + cluster)             (영상 + 인플루언서 EDA)
        │                                         │
        └──────────┬─────────────┬────────────────┘
                   │             │
                   ▼             ▼
        notebooks/amazon_tiktok/    notebooks/tiktok/
        05_without_wonyoung_main    tiktok_marketing_modeling_v2
        (Amazon × TikTok 결합)      (PSM ATT: 4.76%p)
                   │                          │
                   └──────────┬───────────────┘
                              ▼
                  notebooks/tiktok/tiktok_statistic_analysis
                  (within-FE: selection effect 95% 발견)
                              │
                              ▼
                  notebooks/tiktok/tiktoker_recommend
                  (ver.1 → ver.4 추천 알고리즘)


┌─────────────────────────────────────────────────────────────────┐
│              GraphRAG 챗봇 (별개 파이프라인)                      │
│                                                                  │
│  Amazon 리뷰 + TikTok 메타 → entity 추출                         │
│  (BRAND 5 + TYPE 46 + INGREDIENT 498 + EFFECT 23 = 약 570 노드)  │
│                            ↓                                     │
│  Microsoft GraphRAG → LanceDB 벡터 인덱스                        │
│                            ↓                                     │
│  src/rag_chatbot/                                                │
│  ├─ ollama/ (gemma2, 로컬)                                       │
│  └─ cosmetic_rag_chat/ (gpt-3.5-turbo, OpenAI)                   │
│                            ↓                                     │
│  Multi-hop 질의 (예: "보습에 좋은 히알루론산 함유 제품")         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. 결론

### 4-1. Amazon 갈래 — 가설 깨짐에서 시장 본질, 그리고 USP 까지

**처음 가설**: 경쟁사 5 곳의 리뷰 키워드 빈도가 브랜드마다 다를 것
**Chi-square 검정**: p > 0.9 → **가설 깨짐** (브랜드 안 가리고 키워드 공통)

깨진 자리에서 발견한 패턴 — `redness`, `acne`, `scent`, `dry↔oily` 같은 키워드가 긍·부정 리뷰에 동시 등장 → ***제품 만족이 키워드보다 사용 경험·피부 타입에 더 의존*** 한다는 인사이트.

이 인사이트로 TF-IDF / LDA 토픽 모델 진행 → **경쟁사 분화 축** 확인:
- **Dr.Jart+** = 보습
- **COSRX** = 트러블 케어
- **PURITO** = 천연성분

→ **3-beaty 진출 USP**: *히알루론산 기반 무자극 보습 + 부정 피드백 (Sticky · Irritated · Bottle) 해결 + 피부 타입 세분화 메시지*

→ **GraphRAG 챗봇** 으로 분석 결과를 *질의 가능한 추천 시스템* 으로 옮김 (4 종 entity 노드 약 570 개, multi-hop 질의 지원).

### 4-2. TikTok 갈래 — K-Premium Causal Robustness (selection effect 95% 발견)

| 단계 | 모델 | K-Premium | p-value | 의미 |
| --- | --- | ---: | ---: | --- |
| ① OLS Full | `ERV_w ~ is_generic + is_k_beauty + log_*` | **+5.02 %p** | <0.001 | 일반 회귀 — 인플루언서 selection 포함 |
| ② PSM ATT | 영상 특성 매칭 후 ATT | **+4.76 %p** | <0.01 | 영상 단위 인과 보강 — 인플루언서 selection 미통제 |
| ③ within-influencer FE | LSDV + clustered SE | **+0.24 %p** | 0.75 | **인플루언서 통제 시 효과 사라짐** → selection effect 95% |

→ PSM 으로 영상 특성 매칭해도 selection effect 잡지 못함. **인플루언서 고유 특성** (베이스 ER, 채널 컨셉) 통제하는 within-FE 가 가장 robust 한 인과 추정.

→ 단순 OLS 만 보고 *"K-beauty 키워드 추가 → +5%p"* 결론 냈다면 잘못된 마케팅 권고. **마케팅 핵심 레버: 키워드 → 인플루언서 선정** 으로 이동.

자세한 수치 변천 → [docs/refactor/14_kpremium_number_history.md](docs/refactor/14_kpremium_number_history.md)

### 4-3. Robustness — *"단순 분석의 함정"* 4 사례

selection effect 발견 (사례 ①) 이 우연이 아니라 **broad pattern** 임을 3 개 추가 분석으로 입증:

| 사례 | 단순 분석 결론 | 보강 후 진실 | 발견 |
| --- | --- | --- | --- |
| ① **Cross-sectional OLS vs FE** (메인) | K-keyword +5 %p ✅ | within-influencer 0.24 %p ❌ | selection effect 95% |
| ② **토픽 × ER** | asmr 19.13 vs eating 12.19 (7%p 차이) | 9 토픽 중 8 개 within-FE 유의 X (asmr 만 +2.19 marginal) | selection effect 가 broad pattern |
| ③ **Amazon × TikTok 5-brand matching** | TikTok 화제도 ↑ → Amazon 매출 ↑ 가설 | Spearman = **−0.80** (음의 상관) | Established (COSRX) vs 신생 (PURITO) 양극화 |
| ④ **시계열 lag** | TikTok 가 Amazon 을 leads (마케팅 통념) | Amazon 이 TikTok 을 **약 3 개월 leads** | 인과 방향 역전 |

자세한 분석 → [docs/refactor/13_amazon_tiktok_brand_matching.md](docs/refactor/13_amazon_tiktok_brand_matching.md)

### 4-4. 추천 알고리즘 — 인플루언서 시딩 자동화

selection effect 95% 발견 → 인플루언서 자동 선정이 본 분석의 직접 솔루션. ver.1 → ver.4 progressive evolution:

| 지표 | ver.1 (TF-IDF cosine) | ver.4 (vector scaling + ER% 직접 곱) | 개선 |
| --- | ---: | ---: | ---: |
| 1,540 조합 평균 ERV | 15.0 | 39.1 | +24.1 |
| 무작위 대비 (10K 부트스트랩) | 1.25배 | **3.25배** | — |
| 무작위 평균 이상 비율 | 61.4% | **100%** | — |
| Precision@10 | 20% | **60%** | — |

ver.3 강점 6 + 한계 + ver.4 개선 정량 → [docs/refactor/12_tiktok_recommendation_evolution.md](docs/refactor/12_tiktok_recommendation_evolution.md)

### 4-5. 비즈니스 시사점 + 한계

**시사점**:
- 신규 인플루언서 시딩 시 **K-Beauty 키워드 사용자 우선** (4.76 ~ 5.10 %p 효과가 selection 에 의존)
- 추천 알고리즘 결과를 **마이크로 / 미들 / 매크로 세그먼트** 분리 → 캠페인 목표 (인지도 / 전환 / 브랜드 awareness) 에 맞춰 운영
- 1만뷰당 **47,600 ~ 51,000원** = ERV (참여 행동) 기준 하한 추정 — Amazon 매출 funnel attribution 데이터 추가되면 ROAS / CAC 환산 가능

**한계**:
- **단일 시점 / 데이터셋** (2024.12 수집) — 일반화하려면 추가 수집 필요. TikTok CAPTCHA 으로 표본 확장 비용
- **ERV ≠ 직접 매출** — *관심·반응 신호* 까지만. *참여 → 검색 → Amazon 구매* attribution 데이터 부재
- **추천 알고리즘 평가** — Precision@10 외에 NDCG / MAP / HitRate 같은 ranking quality 표준 metric 보강 여지
- **추천 풀 크기** — 56명 → 수백 ~ 수천명 풀로의 scaling 검증 필요

---

## 5. 분석 깊이 docs (`docs/`)

### `docs/refactor/` — 분석 / 정리 진화 기록

- [12_tiktok_recommendation_evolution.md](docs/refactor/12_tiktok_recommendation_evolution.md) — 추천 알고리즘 ver.1 → ver.4 진화 + 6 강점 + 정량 검증
- [13_amazon_tiktok_brand_matching.md](docs/refactor/13_amazon_tiktok_brand_matching.md) — Amazon × TikTok 5 brand 매칭 + 시계열 lag
- [14_kpremium_number_history.md](docs/refactor/14_kpremium_number_history.md) — K-Premium 수치 변천 (8.43 → 4.76 ~ 5.10 영구 기록)
- [EXPERIMENTS_PLAYBOOK.md](docs/refactor/EXPERIMENTS_PLAYBOOK.md) — 변종 정리 표준 (Pattern A/B/C, in-tree 보존)
- [docs/refactor/](docs/refactor/) 전체 — 정리 토픽별 결정 기록 (01 ~ 14)

### `docs/` — 파이프라인 설계 docs

- [pipeline_overview.md](docs/pipeline_overview.md) — 전체 데이터 파이프라인 개요
- [amazon_crawler.md](docs/amazon_crawler.md) — Amazon Crawler 설계
- [tiktok_crawler.md](docs/tiktok_crawler.md) — TikTok Crawler + 지표 정의
- [etl_pipeline.md](docs/etl_pipeline.md) — ETL + 데이터 적재 프로세스
- [db_schema.md](docs/db_schema.md) — DB 스키마 설계
- [slack_alert.md](docs/slack_alert.md) — Slack 알림 모듈

---

## 6. 기술 스택

**언어 / 데이터**: Python · Pandas · NumPy
**통계 / ML**: scikit-learn · statsmodels (OLS HC3 · PSM · LSDV FE) · gensim · nltk · spaCy
**크롤링**: Selenium · Playwright
**저장소 / 인프라**: MySQL · SQLAlchemy · Docker · Slack incoming webhook
**LLM / RAG**: Microsoft GraphRAG · LanceDB (벡터 스토어) · Ollama (gemma2 + nomic-embed-text) · OpenAI (gpt-3.5-turbo + text-embedding-3-small)
**시각화**: Matplotlib · Seaborn · Plotly · pyLDAvis

---

## 7. 본인 담당 (5 명 팀 · 분석 파트 거의 전부)

| 영역 | 본인 담당 |
| --- | --- |
| 데이터 수집 / 크롤러 | Selenium 으로 Amazon 5 brand 1.2만 + TikTok 4,600 영상 반자동 수집 (CAPTCHA 수동) → 정제 후 56명 인플루언서 1,680 영상으로 분석 |
| DB · 인프라 | MySQL 스키마 + SQLAlchemy upsert + Slack 모니터링 봇 + Docker |
| Amazon 분석 | Chi-square 검정 → TF-IDF / LDA 토픽 모델 → 경쟁사 차별화 축 추출 (gensim · nltk · spaCy) |
| TikTok 인과 추정 | 윈저화 + OLS HC3 + PSM ATT + within-influencer FE 4 단계 (statsmodels) |
| 추천 알고리즘 | TF-IDF + cosine + ER% 가중치 → 1,540 조합 부트스트랩 검증 → 한계 발견 후 재구현 |
| GraphRAG 챗봇 | Microsoft GraphRAG + LanceDB + Ollama / OpenAI 두 변형 비교 |
| 부정어 처리 모듈 | `src/util/negation.py` 4 단계 (NLTK + PMI + 도메인 lexicon + SpaCy) |

**팀원 분담**: 분석 결과 시각화 일부, 발표 자료 디자인, 일부 토픽 라벨링 검수.

---

## 8. 환경 / 재현성

- **Python**: 3.11+
- **의존성**: `requirements.txt` (Pandas · scikit-learn · statsmodels · gensim · nltk · spaCy · Selenium · SQLAlchemy · LanceDB · graphrag 등)
- **MySQL**: Docker container (`docker-compose.yml`)
- **GraphRAG 인덱싱**: 로컬 Ollama (`gemma2` 모델 다운로드 필요) 또는 OpenAI API key
- **TikTok 크롤링**: CAPTCHA 수동 통과 필요 (완전 자동화 X)
- **`.env` 자격증명**: Amazon 계정, MySQL 접속, Slack webhook URL, OpenAI API key

---

## 9. 향후 계획 (Future Works)

### 분석 보강 (외부 데이터 필요)
- TikTok → Amazon attribution 데이터 연결 → ROAS / CAC 환산
- 다른 시점·데이터셋 재수집 → K-Premium 효과 안정성 재검증
- 추천 알고리즘 NDCG / MAP / HitRate 보강 + 56명 → 수백+ scaling 검증

### 엔지니어링
- Large notebook (50MB+) LFS 마이그레이션 또는 outputs cleanup
- Amazon 크롤러 / TikTok 크롤러 docker-compose 통합
- GraphRAG 인덱스 재생성 자동화 (현재는 manual)

---

## License

MIT (별도 명시 없으면).