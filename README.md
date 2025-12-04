# K-Beauty 미국 시장 분석 & 데이터 파이프라인 프로젝트

본 프로젝트는 Amazon 리뷰 데이터와 TikTok 콘텐츠 데이터를 기반으로  
**K-Beauty 브랜드의 미국 시장 전략 수립**을 목표로 진행한 데이터 엔지니어링·분석 프로젝트입니다.

데이터 수집부터 ETL, 저장, 자동화 알림까지 **엔드-투-엔드 데이터 파이프라인**을 직접 구성했습니다.

---

## 🚀 프로젝트 주요 기능

### 1) Amazon 리뷰 · 제품 데이터 크롤링
- Selenium 기반 상세 페이지 크롤러
- 제품 정보, 가격, 성분, Best Seller Rank 수집
- 리뷰 최대 20,000건 수집

### 2) TikTok 콘텐츠 & 인플루언서 데이터 크롤링
- 해시태그 기반 검색
- 영상 정보 / 참여율(ER) / 해시태그 / 텍스트 추출
- 콘텐츠 기반 유사도 분석을 위한 텍스트 전처리

### 3) 모듈형 ETL 파이프라인
- 텍스트 정제
- 필드 정규화
- 스키마 검증(Validation)
- 중복 제거 및 Upsert

### 4) DB 적재(MySQL)
- 제품 테이블(items)
- 리뷰 테이블(reviews)
- 인덱스 기반 upsert 처리

### 5) Slack 자동 알림
- 배치 성공/오류/적재 데이터 개수 알림

---

## 🧱 프로젝트 구조
```
src/
├── amazon_review_crawler/
│ ├── main.py # Amazon 크롤링 메인
│ ├── items.py # 제품 데이터 로더
│ ├── reviews.py # 리뷰 데이터 로더
│ ├── mysql1.py # MySQL Client
│ ├── slack1.py # Slack Notifier
│ ├── old_version_main.py
│ └── .env
└── tiktok_crawler/ (추가 예정)
docs/
├── pipeline_overview.md
├── amazon_crawler.md
├── tiktok_crawler.md
├── etl_pipeline.md
├── slack_alert.md
└── db_schema.md
```
---

## 🎯 분석 목표

- **고객 반응 기반 제품 전략 수립**  
  - Amazon 리뷰 + TikTok 콘텐츠 분석을 통해 소비자 선호·불만 요인 도출

- **데이터 기반 인플루언서 마케팅 효율화**  
  - ER 기반 필터링  
  - 콘텐츠 유사도 기반 타겟팅

- **기업 수익성 향상**  
  - 광고비 효율 증가(ROAS 개선)  
  - 전환율 향상(Conversion ↑)

---

## 🛠 기술 스택

| 영역 | 사용 기술 |
|------|-----------|
| 데이터 수집 | **Selenium, BeautifulSoup, TikTok API(비공식)** |
| ETL | **Pandas, 정규표현식, 데이터 검증 모듈** |
| DB | **MySQL, SQLAlchemy** |
| Alert | **Slack Webhook** |
| 분석 | **TF-IDF, LDA, 클러스터링, GraphRAG** |
| 환경 | Python 3.10, .env 기반 설정 |

---

## 📦 주요 모듈 문서

- [데이터 파이프라인 구조](docs/pipeline_overview.md)  
- [Amazon 크롤러 설명](docs/amazon_crawler.md)  
- [TikTok 크롤러 설명](docs/tiktok_crawler.md)  
- [ETL 처리 구조](docs/etl_pipeline.md)  
- [Slack 알림 연동](docs/slack_alert.md)  
- [DB Schema](docs/db_schema.md)

---

## ▶ 실행 방법

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

## 🏗 향후 발전 계획

- TikTok → Amazon 전환 모델링
- 인플루언서 추천 알고리즘 고도화
- Airflow 기반 배치 스케줄링
- API 기반 실시간 서비스 확장

---

# 📜 License
MIT License


