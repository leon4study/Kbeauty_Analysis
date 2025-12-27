# [←](../README.md) DB Schema 설계

관계형 데이터베이스(MySQL)를 활용하여 제품과 리뷰, 콘텐츠 간의 정규화된 구조를 유지합니다.

### 1. 제품 테이블 (`amazon_items`)

- `asin` (PK, VARCHAR): 아마존 제품 고유 ID
- `brand` (VARCHAR): 브랜드명
- `price` (DECIMAL): 판매 가격
- `ingredients` (TEXT): 전성분 리스트

### 2. 리뷰 테이블 (`amazon_reviews`)

- `review_id` (PK, VARCHAR): 리뷰 고유 ID
- `asin` (FK): 제품 테이블 참조
- `rating` (INT): 소비자 평점 (1-5)
- `content` (TEXT): 정제된 리뷰 본문

### 3. TikTok 콘텐츠 테이블 (`tiktok_contents`)

- `video_id` (PK, VARCHAR): 영상 고유 ID
- `author_id` (VARCHAR): 인플루언서 계정 ID
- `view_cnt`, `like_cnt`, `comment_cnt`, `save_cnt` (BIGINT): 성과 데이터
- `is_k_keyword` (TINYINT): K-Beauty 관련 태그 포함 여부
