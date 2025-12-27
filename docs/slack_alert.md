# [←](../README.md) Slack 알림 모듈

Webhook 기반으로 메시지를 전송합니다.

- **메시지 내용**: 파이프라인 성공/실패 여부, 처리된 아이템/리뷰 건수.
- **사용 예시**:
  - `✅ items: 325 rows inserted`
  - `❌ error: TimeoutException`

## 사용 예시 zhem

```python
from slack1 import send_msg
send_msg("크롤링 완료!")
```
