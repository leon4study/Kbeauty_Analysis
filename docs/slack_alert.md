# [←](../README.md) Slack 알림 모듈

아마존 크롤러 파이프라인의 성공/실패 알림을 Slack Webhook 으로 전송하는 모듈.

- **위치**: `src/amazon_review_crawler/` (크롤러 내부에서 직접 호출)
- **메시지 내용**: 파이프라인 성공/실패 여부, 처리된 아이템/리뷰 건수.
- **트리거 예시**:
  - `✅ items: 325 rows inserted`
  - `❌ error: TimeoutException`

## 사용 예시

```python
from slack1 import send_msg
send_msg("크롤링 완료!")
```

## 환경 설정

Webhook URL 은 환경변수 또는 `.env` 파일로 관리:

```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

## 관련 파일

- `src/amazon_review_crawler/main.py` — 크롤링 완료/실패 시 `send_msg()` 호출
- `.env.example` — Webhook URL 환경변수 예시 포함
