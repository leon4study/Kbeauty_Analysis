# K-Beauty 미국 시장 분석 (Kbeauty_Analysis)

신규 인디 K-Beauty 브랜드의 미국 Amazon 시장 진출 전략을 Amazon 경쟁사 리뷰와 TikTok 인플루언서 데이터를 통합 분석해 데이터로 설계한 엔드투엔드 프로젝트.

신규 인디 브랜드 *3-beaty* (히알루론산 기반, Torriden 을 reference 로 한 가상 페르소나) 의 미국 Amazon 진출을 두 가지 분석으로 풀었습니다.

**Amazon - 경쟁사 리뷰 분석으로 진출 빈자리 찾기**

경쟁사 5 곳의 리뷰 1.2만 건을 분석했습니다. 처음 가설 *(브랜드별 키워드 빈도가 다를 것)* 이 Chi-square 검정에서 p > 0.9 로 깨졌고, 그 자리에서 *제품 만족이 키워드보다 사용 경험·피부 타입에 더 의존* 한다는 시장 본질을 잡았습니다. 이 인사이트로 TF-IDF / LDA 토픽 모델까지 들어가 *경쟁사들이 어떤 부분으로 차별화하는지* (Dr.Jart+ 보습 / COSRX 트러블 케어 / PURITO 천연성분) 확인했고, 3-beaty 의 차별화 포인트를 *히알루론산 기반 무자극 보습 + 경쟁사 공통 단점 (Sticky · Irritated) 보완* 으로 정의했습니다.

**TikTok - 마케팅 효과 정량 검증**

*K-Beauty 마케팅이 Amazon 매출로 연결되는가* 를 정량으로 검증했습니다. 키워드 기반으로 약 6,500 영상 (인플루언서 3,300+ 명) 을 1차 수집한 뒤, 분석 표본 확보를 위해 56명 인플루언서로 좁혀 인플루언서당 30 영상씩 추가 수집해 1,680 영상으로 분석에 들어갔습니다. OLS → 매칭 기반 인과 추정 (PSM) → 같은 인플루언서 안에서만 비교하는 within-influencer Fixed Effect 까지 4 단계 회귀로 K-Premium 4.76 ~ 5.10 %p 를 추정했는데, 마지막 within-FE 단계에서 그 효과의 약 95% 가 *인플루언서 selection effect* 임이 드러났습니다. 마케팅의 핵심 레버가 *키워드* 가 아니라 *인플루언서 선정* 이라는 결론으로 넘어갔고, 이 selection 을 자동화하기 위해 추천 알고리즘을 ver.1 부터 ver.4 까지 진화시켜 1,540 조합 부트스트랩 검증에서 무작위 대비 1.25배에서 3.25배 ER% 까지 끌어올렸습니다.

---

## 분석 핵심 결과

| 결과 | 수치 | 의미 |
| --- | --- | --- |
| K-Premium ERV 효과 | **+4.76 ~ 5.10 %p** | TikTok 영상에 K-Beauty 해시태그가 들어가면 ERV (참여율 = 좋아요·댓글·저장 / 조회수) 가 비-K-Beauty 영상 대비 4.76~5.10%p 더 높음 (윈저화 OLS HC3 / PSM ATT 두 추정의 하한·상한) |
| Selection effect | **95%** | 위 K-Premium 효과의 95% 가 *K-Beauty 키워드를 쓰는 인플루언서들이 원래부터 인기 있는 사람들* 이라는 점에서 옴 (같은 인플루언서 안에서 비교한 within-FE 시 키워드 자체 효과는 통계적 유의 X). **마케팅 핵심 레버는 키워드보다 인플루언서 선정** |
| 추천 알고리즘 ver.4 | **무작위 대비 3.25배** | 56명 인플루언서 중 2명을 시드로 ver.4 알고리즘이 나머지를 추천했을 때, Top-10 인플루언서의 ER% (참여율) 평균이 무작위 추천 대비 3.25배. 1,540 가지 모든 조합으로 부트스트랩 검증 |
| 1만뷰당 환산 가치 | **47,600 ~ 51,000원** | K-Premium 효과를 *참여 1건당 100원* 가정 시 1만뷰당 추가 가치 |

→ selection effect 95% 발견 방법론 (추가 데이터 수집 + within-FE) 자세히: [`docs/refactor/14`](docs/refactor/14_kpremium_number_history.md)
→ 단계별 표 + Robustness 4 사례 + 추천 알고리즘 ver.1 → ver.4 진화 자세히: [`docs/refactor/`](docs/refactor/)

---

## 데이터 파이프라인 (개요)

```
[Amazon 5 brand]               [TikTok 4 keyword]
       │                              │
       ▼                              ▼
  src/amazon_                   src/tiktok_
  review_crawler/               crawler/
       │                              │
       ▼                              ▼
  data/bronze/amazon/           data/bronze/tiktok/
  (raw 수집 CSV)                 (raw 수집 CSV)
       │                              │
       ▼                              ▼
  data/silver/amazon/           data/silver/tiktok/       ← src/pipelines/
  (전처리 bridge)                (정제 통합본)               build_silver_amazon.py
                                                              build_silver_tiktok.py
       │                              │
       ▼                              ▼
  notebooks/amazon/             notebooks/tiktok/
  01 전처리 → 02 EDA            EDA + topic + recommend
  → 03 LDA 토픽 모델                  │
       │                              │
       └──────────────┬───────────────┘
                      ▼
            notebooks/amazon_tiktok/
            (K-Premium 결합 분석)
                      ▼
            notebooks/tiktok/
            tiktok_statistic_analysis
            (within-FE → selection effect 95%)
                      ▼
            notebooks/tiktok/
            tiktoker_recommend
            (추천 알고리즘 ver.4)


[GraphRAG 챗봇 — 별개 인덱싱]
Amazon 제품·성분·효과 데이터
       ▼
Microsoft GraphRAG 인덱싱 → LanceDB
       ▼
src/rag_chatbot/ (Ollama / OpenAI 두 변형)
```

→ 코드 자세히: [`src/README.md`](src/README.md)
→ 노트북 카탈로그: [`notebooks/tiktok/README.md`](notebooks/tiktok/README.md), [`notebooks/amazon_tiktok/README.md`](notebooks/amazon_tiktok/README.md), [`notebooks/amazon/`](notebooks/amazon/)

---

## 메인 서비스 — 개인 맞춤 화장품 추천 챗봇

분석 결과에서 모은 *제품·성분·효과·피부 타입* 정보를 활용해, 고객이 자기 조건으로 화장품을 추천받을 수 있는 챗봇을 구축했습니다.

**사용 시나리오 예시**:

- *"건성 피부에 맞는 보습 크림 추천해줘"*
- *"알코올 성분 없는 클렌저 알려줘"*
- *"파라벤 알러지 있는데 안전한 제품?"*
- *"민감 피부에 맞는 히알루론산 함유 제품"*

**구조**: Microsoft GraphRAG + LanceDB 벡터 스토어 위에 약 570 개 노드 (브랜드 5 + 제품 타입 46 + 성분 498 + 효과 23) 의 지식 그래프를 구축. 단순 키워드 검색이 아니라 *"민감 피부 + 히알루론산 + 알코올 제외"* 같이 여러 조건이 얽힌 multi-hop 질의가 가능합니다.

**메인 챗봇**: GraphRAG + OpenAI (gpt-4o-mini) — 정확도 + 안정성
→ [`src/rag_chatbot/cosmetic_rag_chat/README.md`](src/rag_chatbot/cosmetic_rag_chat/README.md) (인덱싱 1회 ~$0.06, query 거의 무료)

**실험 변형** (PR #32 실측 비교 — 트레이드오프 발견):
- LightRAG (Gemini Tier 1 무료) → 응답 품질 우세, [`src/rag_chatbot/lightrag_variant/README.md`](src/rag_chatbot/lightrag_variant/README.md)
- GraphRAG (위 메인) → 안전성 11배 우세 (알러지 회피 등)
- 비교 결과: [`docs/rag_evaluation_results.md`](docs/rag_evaluation_results.md)
- Ollama 변형 (archived) → [`src/rag_chatbot/_experimental/ollama/README.md`](src/rag_chatbot/_experimental/ollama/README.md)

### Fresh clone 빠른 시작 (메인 — OpenAI)

```bash
git clone <repo>
cd Kbeauty_Analysis
pip install -e .
cp .env.example .env   # OPENAI_API_KEY 채우기
cp examples/graphrag_input/brand_50_sample.txt \
   src/rag_chatbot/cosmetic_rag_chat/indexing/input/
graphrag index --root ./src/rag_chatbot/cosmetic_rag_chat/indexing   # 수 분
python -m src.rag_chatbot.cosmetic_rag_chat.main --method local
```

→ `http://127.0.0.1:7860` 에서 챗봇 사용. 인덱싱 데이터는 `examples/graphrag_input/` 에 git 포함.

---

## 프로젝트 구조

```
src/
  amazon_review_crawler/   Amazon 리뷰 크롤러 (Selenium + MySQL)
  tiktok_crawler/          TikTok 영상 크롤러 (Selenium 반자동)
  pipelines/               데이터 파이프라인 (bronze → silver 변환)
  rag_chatbot/             개인 맞춤 추천 챗봇
    cosmetic_rag_chat/     메인 (GraphRAG + OpenAI)
    lightrag_variant/      실험 (LightRAG + Groq/Gemini 무료)
    graphrag_viewer/       GraphRAG 결과 네트워크 시각화
    _experimental/ollama/  archived — 옛 Ollama 변형 (호환성 issue)
  util/                    공통 유틸리티 (경로·부정어 처리·Slack)
notebooks/
  EDA.ipynb                Amazon 5 brand EDA
  amazon/                  Amazon 분석 3단계 (전처리 → EDA → LDA)
    01_amazon_preprocessing.ipynb
    02_amazon_eda.ipynb
    03_amazon_topic_modeling.ipynb
  tiktok/                  TikTok 분석 (7 노트북, 01-07 실행 순서)
  amazon_tiktok/           Amazon × TikTok 결합 (2 메인 + experiments/ 4)
  archive/                 분할 전 원본 보존 (lemmatized_full_pipeline 등)
docs/
  refactor/                분석 깊이 영구 기록 (12~16)
  pipeline_overview.md     전체 파이프라인 개요
  amazon_crawler.md, ...   각 모듈 설계 docs
data/
  bronze/                  수집 원본 (amazon/ · tiktok/, README 포함)
  silver/                  정제 통합본 (amazon/ · tiktok/)
  gold/                    최종 분석 결과 (amazon/lda_topics_overall.csv, tiktok/dashboards/)
  model/                   GraphRAG 인덱스 (LanceDB)
  References/              참고 논문 PDF
  archive/                 재현 불가 artifact 보존 (legacy intermediate / orphan outputs)
```

---

## 자세히 보기

- **코드 모듈 카탈로그**: [`src/README.md`](src/README.md)
- **노트북 카탈로그**:
  - [`notebooks/amazon/README.md`](notebooks/amazon/README.md) — Amazon 분석 3단계 (01 전처리 → 02 EDA → 03 LDA)
  - [`notebooks/tiktok/README.md`](notebooks/tiktok/README.md) — TikTok 분석 7 노트북 (01-07)
  - [`notebooks/amazon_tiktok/README.md`](notebooks/amazon_tiktok/README.md) — Amazon × TikTok 결합 (2 메인 + 4 experiments)
- **추천 챗봇 실행**:
  - [`src/rag_chatbot/cosmetic_rag_chat/README.md`](src/rag_chatbot/cosmetic_rag_chat/README.md) — **메인** (GraphRAG + OpenAI)
  - [`src/rag_chatbot/lightrag_variant/README.md`](src/rag_chatbot/lightrag_variant/README.md) — 실험 (LightRAG + Groq/Gemini 무료)
  - [`src/rag_chatbot/_experimental/ollama/README.md`](src/rag_chatbot/_experimental/ollama/README.md) — archived (옛 Ollama 변형)
- **분석 기법 설명** (`docs/methods/`):
  - [PSM + Within-FE](docs/methods/psm_within_fe.md) — TikTok K-Premium 분석의 인과 추정 기법 (selection effect 95% 발견의 *방법론적 기반*). 교과서적 설명 + 본 프로젝트 적용 + 한계
  - [BM25 — TF-IDF 대체 검토](docs/bm25_for_tfidf_consideration.md) — 미래 보강 옵션. 현재 TF-IDF 사용처 + BM25 적용 시 효과 평가
- **분석 깊이 docs** (작업 과정 history):
  - [12 — 추천 알고리즘 ver.1 → ver.4 진화 + 정량 검증](docs/refactor/12_tiktok_recommendation_evolution.md)
  - [13 — Amazon × TikTok 5 brand matching + 시계열 lag](docs/refactor/13_amazon_tiktok_brand_matching.md)
  - [14 — K-Premium 수치 변천 (8.43 → 4.76 ~ 5.10) 영구 기록](docs/refactor/14_kpremium_number_history.md)
  - [16 — silver 단계 설계 + historical artifact 보존](docs/refactor/16_silver_artifact_origin.md)
  - [17 — 2026-05 medallion 마무리 + data legacy + 온보딩 정리 (PR #5~#14 종합)](docs/refactor/17_2026_05_session_cleanup.md)
  - [18 — H1+H2 리팩터링: for-loop 벡터화 + Selenium 상수 정리](docs/refactor/18_vectorization_and_constants.md)
  - [EXPERIMENTS_PLAYBOOK](docs/refactor/EXPERIMENTS_PLAYBOOK.md) — 변종 정리 표준
- **파이프라인 설계 docs**:
  - [pipeline_overview](docs/pipeline_overview.md), [amazon_crawler](docs/amazon_crawler.md), [tiktok_crawler](docs/tiktok_crawler.md)
  - [etl_pipeline](docs/etl_pipeline.md), [db_schema](docs/db_schema.md), [slack_alert](docs/slack_alert.md)
- **RAG 챗봇 평가**:
  - [rag_evaluation_framework](docs/rag_evaluation_framework.md) — 5 차원 metric (retrieval / generation / 실용 / 도메인 / 일관성) + RAGAS 활용
  - [lightrag_comparison_design](docs/lightrag_comparison_design.md) — LightRAG 변형 *시도* 기록 (메인 GraphRAG 와 비교 실험)
  - [setup_lightrag_env](docs/setup_lightrag_env.md) — LightRAG 변형 사용 시 별도 venv 안내
  - [rag_evaluation_results](docs/rag_evaluation_results.md) — provider 비교 표 (OpenAI / Groq / Gemini), 비용/latency/faithfulness trade-off
  - [examples/graphrag_configs/](examples/graphrag_configs/) — provider 별 settings.yaml 템플릿 (Groq / Gemini 무료 변형)
  - [tests/rag_eval/](tests/rag_eval/) — golden 10 질문 + evaluate.py 평가 하네스

---

## License

MIT (별도 LICENSE 파일 추가 예정)
