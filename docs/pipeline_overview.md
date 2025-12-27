# [←](../README.md) 전체 파이프라인 구조 (Pipeline Overview)

본 프로젝트는 데이터 수집부터 최종 인사이트 도출까지 4개 단계의 엔드투엔드 흐름을 가집니다.

### 1. 데이터 수집 단계 (Data Collection)

- **Amazon**: Selenium을 활용하여 제품 메타데이터와 리뷰 텍스트를 수집합니다.
- **TikTok**: 해시태그 기반으로 조회수, 참여도(좋아요, 댓글, 저장), 인플루언서 정보를 수집합니다. 플랫폼 제약으로 인해 수동 세션 인증을 거친 반자동 수집 방식을 사용합니다.

### 2. 데이터 가공 단계 (ETL & Normalization)

- 수집된 Raw Data를 `src/amazon_review_crawler/reviews.py` 모듈을 통해 정문화합니다.
- 번역, 형태소 분석, Lemmatization, N-gram 생성을 거쳐 분석 가능한 텍스트 데이터로 변환합니다.

### 3. 데이터 적재 단계 (Storage)

- SQLAlchemy 유틸리티를 활용하여 MySQL 데이터베이스에 적재합니다.
- Upsert 로직을 구현하여 중복 수집을 방지하고 최신 성과(조회수 등)를 업데이트합니다.

### 4. 분석 및 서빙 단계 (Analysis & Serving)

- **통계 분석**: ER, ERV 지표를 생성하고 OLS 회귀 분석을 통해 K-Premium을 산출합니다.
- **NLP 분석**: LDA 토픽 모델링으로 소비자 미충족 수요(Unmet Needs)를 도출하고, GraphRAG로 지식그래프 기반 Q&A 프로토타입을 구동합니다.
- **모니터링**: Slack Webhook을 연동하여 배치 프로세스의 성공/실패 여부를 실시간으로 알립니다.
