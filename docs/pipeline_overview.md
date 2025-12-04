# 데이터 파이프라인 구조

본 프로젝트의 파이프라인은 다음 단계를 포함합니다.

```
Crawler → Transform → Validation → Load(MySQL) → Slack 알림
```

## 1) Crawler

- Amazon / TikTok 크롤링
- Selenium + 대량 스크롤 + 상세 페이지 크롤링
- JSON 형태로 수집

## 2) Transform

- 텍스트 정제
- 날짜 포맷 통일
- 가격/리뷰/평점 형 변환
- dict 계층화 및 JSON 직렬화

## 3) Validation

- 중복 제거
- 필수 필드 검증
- 리뷰·제품 스키마 검사

## 4) Load(MySQL)

- items 테이블 upsert
- reviews 테이블 upsert
- 키 충돌 시 delete 후 insert 처리

## 5) Slack 알림

- 성공/실패/처리 건수 자동 메시지
