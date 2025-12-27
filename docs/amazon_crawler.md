# [←](../README.md) Amazon Crawler 설계

Amazon의 동적 웹 페이지 구조를 고려하여 Selenium 기반으로 설계된 크롤러 모듈입니다.

### 1. 수집 전략

- **제품 정보**: ASIN을 기반으로 제품명, 브랜드, 가격, 전체 평점, 성분 리스트(Ingredients)를 파싱합니다. 특히 성분 데이터는 GraphRAG 엔티티 추출의 핵심 소스로 사용됩니다.
- **리뷰 정보**: 제품 상세 페이지에서 전체 리뷰 페이지로 진입하여 스크롤 및 페이지네이션 로직을 통해 데이터를 확보합니다.

### 2. 주요 클래스 및 함수 (`items.py`, `reviews.py`)

- `ItemsParser`: 제품 상세 페이지에서 CSS Selector를 활용해 메타데이터를 추출합니다. Sponsored 광고 상품을 필터링하는 로직이 포함되어 있습니다.
- `ReviewsParser`: 리뷰 본문, 평점, 작성 날짜를 추출하며, 텍스트 내 이모티콘 제거 및 특수문자 정제 기능을 제공합니다.

#### 2.1 코드 구조

```txt
main.py
│
├── amazon_login()
├── select_best_sellers()
├── get_description()
├── crawl_amazon() ← 전체 크롤링 파이프라인
│
├── load_items()
└── load_reviews()
```

### 3. 기술적 이슈 해결

- **Anti-Bot 대응**: 무작위 User-Agent 전환 및 페이지 로드 대기(Explicit/Implicit Wait) 로직을 적용하였습니다.
- **동적 로딩**: 스크롤 단계별 제어를 통해 모든 리뷰 컨텐츠가 돔(DOM)에 로드된 후 수집을 시작합니다.
