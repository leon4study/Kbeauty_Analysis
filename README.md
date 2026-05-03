# K-Beauty 미국 시장 분석 (Kbeauty_Analysis)

신규 인디 K-Beauty 브랜드의 미국 Amazon 시장 진출 전략을 Amazon 경쟁사 리뷰와 TikTok 인플루언서 데이터를 통합 분석해 데이터로 설계한 엔드투엔드 프로젝트.

신규 인디 브랜드 *3-beaty* (히알루론산 기반, Torriden 을 reference 로 한 가상 페르소나) 의 미국 Amazon 진출을 두 가지 분석으로 풀었습니다.

**Amazon - 경쟁사 리뷰 분석으로 진출 빈자리 찾기**

경쟁사 5 곳의 리뷰 1.2만 건을 분석했습니다. 처음 가설 *(브랜드별 키워드 빈도가 다를 것)* 이 Chi-square 검정에서 p > 0.9 로 깨졌고, 그 자리에서 *제품 만족이 키워드보다 사용 경험·피부 타입에 더 의존* 한다는 시장 본질을 잡았습니다. 이 인사이트로 TF-IDF / LDA 토픽 모델까지 들어가 *경쟁사들이 어떤 부분으로 차별화하는지* (Dr.Jart+ 보습 / COSRX 트러블 케어 / PURITO 천연성분) 확인했고, 3-beaty 의 차별화 포인트를 *히알루론산 기반 무자극 보습 + 부정 피드백 (Sticky · Irritated) 해결* 로 정의했습니다.

**TikTok - 마케팅 효과 정량 검증**

*K-Beauty 마케팅이 Amazon 매출로 연결되는가* 를 정량으로 검증했습니다. 약 4,600 영상을 반자동 수집한 뒤 정제·필터를 거쳐 56명 인플루언서의 1,680 영상으로 분석에 들어갔습니다. OLS → 매칭 기반 인과 추정 (PSM) → 같은 인플루언서 안에서만 비교하는 within-influencer Fixed Effect 까지 4 단계 회귀로 K-Premium 4.76 ~ 5.10 %p 를 추정했는데, 마지막 within-FE 단계에서 그 효과의 약 95% 가 *인플루언서 selection effect* 임이 드러났습니다. 마케팅의 핵심 레버가 *키워드* 가 아니라 *인플루언서 선정* 이라는 결론으로 넘어갔고, 이 selection 을 자동화하기 위해 추천 알고리즘을 ver.1 부터 ver.4 까지 진화시켜 1,540 조합 부트스트랩 검증에서 무작위 대비 1.25배에서 3.25배 ER% 까지 끌어올렸습니다.

---

## 메인 서비스 — 개인 맞춤 화장품 추천 챗봇

분석 결과에서 모은 *제품·성분·효과·피부 타입* 정보를 활용해, 고객이 자기 조건으로 화장품을 추천받을 수 있는 챗봇을 구축했습니다.

**사용 시나리오 예시**:

- *"건성 피부에 맞는 보습 크림 추천해줘"*
- *"알코올 성분 없는 클렌저 알려줘"*
- *"파라벤 알러지 있는데 안전한 제품?"*
- *"민감 피부에 맞는 히알루론산 함유 제품"*

**구조**: Microsoft GraphRAG + LanceDB 벡터 스토어 위에 약 570 개 노드 (브랜드 5 + 제품 타입 46 + 성분 498 + 효과 23) 의 지식 그래프를 구축. 단순 키워드 검색이 아니라 *"민감 피부 + 히알루론산 + 알코올 제외"* 같이 여러 조건이 얽힌 multi-hop 질의가 가능합니다.

**기술 변형 두 가지** (분리 실행해 비교):

- 로컬 Ollama (gemma2) — 비용·프라이버시 이점
- OpenAI (gpt-3.5-turbo) — 정확도

→ 실행 방법: [`src/rag_chatbot/ollama/README.md`](src/rag_chatbot/ollama/README.md)

---

## 분석 핵심 결과

| 결과 | 수치 | 의미 |
| --- | --- | --- |
| K-Premium ERV 효과 | **+4.76 ~ 5.10 %p** | TikTok K-Beauty 키워드의 참여율 효과 (윈저화 OLS HC3 / PSM ATT) |
| Selection effect | **95%** | 그 효과의 95% 가 *인플루언서 selection* 에서. 마케팅 레버가 키워드 → 인플루언서 선정으로 |
| 추천 알고리즘 ver.4 | **무작위 대비 3.25배** ER% | 1,540 조합 부트스트랩 검증 (Top-10 기준) |
| 1만뷰당 환산 가치 | 47,600 ~ 51,000원 | 참여 1건당 100원 가정 |

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
  data/amazon/                  data/tiktok/
       │                              │
       ▼                              ▼
  notebooks/                    notebooks/tiktok/
  EDA + lemmatized_             EDA + topic + recommend
  full_pipeline                       │
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
→ 노트북 카탈로그: [`notebooks/tiktok/README.md`](notebooks/tiktok/README.md), [`notebooks/amazon_tiktok/README.md`](notebooks/amazon_tiktok/README.md)

---

## 프로젝트 구조

```
src/
  amazon_review_crawler/   Amazon 리뷰 크롤러 (Selenium)
  tiktok_crawler/          TikTok 영상 크롤러 (Selenium 반자동)
  rag_chatbot/             개인 맞춤 추천 챗봇 (GraphRAG)
    ollama/                로컬 LLM 변형
    cosmetic_rag_chat/     OpenAI 변형
  util/                    공통 유틸리티 (경로·부정어 처리·Slack)
notebooks/
  EDA.ipynb                Amazon 5 brand EDA
  lemmatized_full_pipeline Amazon 전처리 + LDA 토픽 모델
  tiktok/                  TikTok 분석 (8 노트북)
  amazon_tiktok/           Amazon × TikTok 결합 분석 (7 노트북)
docs/
  refactor/                분석 깊이 영구 기록 (12, 13, 14)
  pipeline_overview.md     전체 파이프라인 개요
  amazon_crawler.md, ...   각 모듈 설계 docs
data/
  amazon/                  수집 리뷰 + 제품 데이터
  tiktok/                  수집 영상 데이터
  model/                   GraphRAG 인덱스
```

---

## 자세히 보기

- **코드 모듈 카탈로그**: [`src/README.md`](src/README.md)
- **노트북 카탈로그**:
  - [`notebooks/tiktok/README.md`](notebooks/tiktok/README.md) — TikTok 분석 8 노트북
  - [`notebooks/amazon_tiktok/README.md`](notebooks/amazon_tiktok/README.md) — Amazon × TikTok 결합 7 노트북
- **추천 챗봇 실행**: [`src/rag_chatbot/ollama/README.md`](src/rag_chatbot/ollama/README.md)
- **분석 깊이 docs**:
  - [12 — 추천 알고리즘 ver.1 → ver.4 진화 + 정량 검증](docs/refactor/12_tiktok_recommendation_evolution.md)
  - [13 — Amazon × TikTok 5 brand matching + 시계열 lag](docs/refactor/13_amazon_tiktok_brand_matching.md)
  - [14 — K-Premium 수치 변천 (8.43 → 4.76 ~ 5.10) 영구 기록](docs/refactor/14_kpremium_number_history.md)
  - [EXPERIMENTS_PLAYBOOK](docs/refactor/EXPERIMENTS_PLAYBOOK.md) — 변종 정리 표준
- **파이프라인 설계 docs**:
  - [pipeline_overview](docs/pipeline_overview.md), [amazon_crawler](docs/amazon_crawler.md), [tiktok_crawler](docs/tiktok_crawler.md)
  - [etl_pipeline](docs/etl_pipeline.md), [db_schema](docs/db_schema.md), [slack_alert](docs/slack_alert.md)

---

## License

MIT (별도 LICENSE 파일 추가 예정)
