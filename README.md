# K-Beauty 미국 시장 분석 & 데이터 파이프라인 (Kbeauty_Analysis)

**서론**  
Amazon 리뷰 + TikTok 콘텐츠를 자동 수집·정제·적재하여 TF-IDF/LDA/GraphRAG 기반 분석과 인플루언서 추천·대시보드 연동까지 수행한 엔드투엔드 데이터 파이프라인.

---

## 🚀 프로젝트 핵심 요약

- Amazon 리뷰 최대 20,000건 수집
- TikTok 콘텐츠 기반 참여율(ER)·해시태그·텍스트 분석
- 모듈형 ETL 파이프라인 구축
- MySQL 기반 정규화 테이블 + Upsert 처리
- 배치 상태 Slack 자동 알림
- TF-IDF / LDA / GraphRAG 기반 텍스트 분석 확장

---

## 🔍 문제 정의

- 미국 Amazon에서 잘 팔리는 K-Beauty 제품이 한국과는 다른 소비자 반응 패턴을 보이는 이유는 무엇인가?
- TikTok 콘텐츠 반응이 실제 제품 관심·구매 전환과 어떻게 연결되는가?
- 인플루언서 마케팅을 데이터로 구조화할 수 있는가?

---

## 🧱 프로젝트 구조

```
Kbeauty_Analysis/
├── src/
│   ├── amazon_review_crawler/
│   │   ├── main.py                # Amazon 크롤링 엔트리포인트
│   │   ├── items.py               # 제품 데이터 수집
│   │   ├── reviews.py             # 리뷰 데이터 수집
│   │   ├── mysql1.py              # MySQL 연결 및 upsert 로직
│   │   ├── old_version_main.py
│   │   └── .env
│   │
│   ├── graphRAG_gradio/
│   │   └── graphRAG_gradio.py     # 리뷰/텍스트 기반 GraphRAG 데모
│   │
│   └── notebooks/
│       ├── EDA.ipynb
│       ├── amazon_tiktok_statistic_analysis.ipynb
│       └── results/
│           ├── ldavis_prepared_*.html
│
├── data/
│   ├── amazon/
│   └── tiktok/
│
├── docs/
│   ├── pipeline_overview.md
│   ├── amazon_crawler.md
│   ├── tiktok_crawler.md
│   ├── etl_pipeline.md
│   └── slack_alert.md
│
├── README.md
└── .gitignore

```

---

## 🔄 데이터 파이프라인 개요

1. 데이터 수집
   - Amazon: Selenium 기반 상세 페이지 크롤링
   - TikTok: 해시태그 기반 콘텐츠 수집
2. ETL 처리
   - 텍스트 정제 및 정규화
   - 컬럼 스키마 검증
   - 중복 제거
   - 키 기반 Upsert
3. 저장
   - MySQL (items / reviews 테이블 분리)
   - 인덱스 기반 성능 최적화
4. 분석
   - TF-IDF 기반 키워드 분석
   - LDA 토픽 모델링 (pyLDAvis 결과 포함)
   - GraphRAG 기반 리뷰 지식 구조화
5. 운영
   - Slack Webhook을 통한 배치 성공/실패 알림

---

## 📊 분석 및 활용 예시

- Amazon 리뷰 토픽 → 제품 개선 포인트 도출
- TikTok 콘텐츠 반응 → 마케팅 메시지 최적화
- 콘텐츠 유사도 기반 → 브랜드 적합 인플루언서 선별
- 리뷰 + 콘텐츠 결합 → 시장 반응 조기 탐지

---

## 🛠 기술 스택

| 영역     | 사용 기술                       |
| -------- | ------------------------------- |
| Crawling | Selenium, BeautifulSoup         |
| ETL      | Pandas, Regex, Validation Logic |
| DB       | MySQL, SQLAlchemy               |
| 분석     | TF-IDF, LDA, GraphRAG           |
| Alert    | Slack Webhook                   |
| 환경     | Python 3.10, `.env`             |

---

## 📦 문서 바로가기

- [데이터 파이프라인 구조](docs/pipeline_overview.md)
- [Amazon 크롤러 설명](docs/amazon_crawler.md)
- [TikTok 크롤러 설명](docs/tiktok_crawler.md)
- [ETL 처리 구조](docs/etl_pipeline.md)
- [Slack 알림 연동](docs/slack_alert.md)
- [DB Schema](docs/db_schema.md)

---

## ▶ 아마존 크롤러 실행 방법

### 1) 환경 변수 설정

`.env` 파일 생성:

```
ID=xxxx
PW=xxxx
DB_SERVER_HOST=xxxx
DB_USERNAME=xxxx
DB_PASSWORD=xxxx
DB_DATABASE=xxxx
DB_PORT=3306
SLACK_WEBHOOK_URL=xxxx
```

### 2) Amazon 크롤러 실행

```
python src/amazon_review_crawler/main.py
```

### 3) Slack 알림 자동 도착

- 크롤링 시작
- 성공적 적재
- 오류 발생 시 스택트레이스 포함 메시지 전송

---

## 🏗 향후 확장 계획

- TikTok → Amazon 전환 모델링
- 인플루언서 추천 알고리즘 고도화
- Airflow 기반 배치 스케줄링
- API 기반 실시간 서비스 확장

---

# 📜 License

MIT License
