# [←](../README.md) DB Schema 설계

관계형 데이터베이스(MySQL)를 활용하여 제품과 리뷰, 콘텐츠 간의 정규화된 구조를 유지합니다.

> 현재 프로젝트는 CSV/Parquet 기반 로컬 분석 파이프라인으로 운영 중.
> 이 스키마는 서비스 확장 시 MySQL 마이그레이션 설계 기준.

## 1. 제품 테이블 (`amazon_items`)

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `asin` | VARCHAR PK | 아마존 제품 고유 ID |
| `brand` | VARCHAR | 브랜드명 (COSRX / PURITO / BeautyOfJoseon / ImFrom / DrJart) |
| `name` | TEXT | 제품명 |
| `price` | DECIMAL | 판매 가격 (USD) |
| `rating` | DECIMAL | 평균 평점 (1.0~5.0) |
| `review_cnt` | INT | 리뷰 수 |
| `ingredients` | TEXT | 전성분 리스트 (원문) |
| `description` | TEXT | 제품 설명 (크롤링 원문) |

## 2. 리뷰 테이블 (`amazon_reviews`)

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `review_id` | VARCHAR PK | 리뷰 고유 ID |
| `asin` | VARCHAR FK | 제품 테이블 참조 |
| `rating` | DECIMAL | 소비자 평점 (1.0~5.0) |
| `date` | DATE | 리뷰 작성일 |
| `content` | TEXT | 리뷰 원문 |
| `lemmatized_review` | TEXT | 전처리 완료 리뷰 (NLTK lemmatize + bigram) |
| `is_sponsored` | TINYINT | 스폰서 리뷰 여부 (1/0) |

## 3. TikTok 콘텐츠 테이블 (`tiktok_contents`)

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `video_id` | VARCHAR PK | 영상 고유 ID |
| `tiktoker_name` | VARCHAR | 인플루언서 계정명 |
| `search_term` | VARCHAR | 크롤링 검색어 |
| `upload_date` | DATE | 업로드 날짜 |
| `like_cnt` | BIGINT | 좋아요 수 |
| `comment_cnt` | BIGINT | 댓글 수 |
| `save_cnt` | BIGINT | 저장 수 |
| `view_cnt` | BIGINT | 조회 수 |
| `is_k_keyword` | TINYINT | K-Beauty 관련 태그 포함 여부 |
| `hash_tag` | TEXT | 해시태그 목록 (공백 구분) |

## 관련 파일

- `data/silver/amazon/` — 현재 실제 데이터 위치 (CSV)
- `data/silver/tiktok/tiktok_videos_silver.csv` — TikTok silver 데이터
- `src/pipelines/build_silver_amazon.py` — Amazon silver 빌드 파이프라인
- `src/amazon_review_crawler/main.py` — 크롤러 (items + reviews 수집)
