# Slack 알림 모듈

Webhook 기반으로 메시지를 전송합니다.

## 사용 예시

```python
from slack1 import send_msg
send_msg("크롤링 완료!")
```

Slack 메시지 예:

```
📌 Pipeline Started
✅ items: 325 rows inserted
❌ error: TimeoutException
```

---

# 📁 **docs/db_schema.md**

```md
# DB Schema

## items 테이블

| 컬럼                | 타입       | 설명      |
| ------------------- | ---------- | --------- |
| ASIN                | String(13) | PK        |
| title               | Text       | 상품명    |
| category            | Text       | 카테고리  |
| brand               | Text       | 브랜드    |
| price               | Float      | 가격      |
| description         | JSON       | 상품 소개 |
| Ingredients         | Text       | 성분      |
| total_star_mean     | Float      | 평균 별점 |
| global_rating_count | Int        | 리뷰 개수 |

---

## reviews 테이블

| 컬럼          | 타입   |
| ------------- | ------ |
| review_num    | PK     |
| ASIN          | FK     |
| customer_id   | String |
| customer_name | Text   |
| title         | Text   |
| date          | Text   |
| review_rating | Float  |
| content       | Text   |
```
