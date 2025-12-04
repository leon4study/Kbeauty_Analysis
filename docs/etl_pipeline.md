# ETL Pipeline 구조

### Transform

- 텍스트 정제(clean_text)
- 컬럼명 통합
- 날짜 포맷 통일
- JSON normalization
- price/score → float 변환

### Validation

- 필드 누락 체크
- rating 범위 검사
- 문자열 길이 검사
- primary key 중복 체크

### Load

- SQLAlchemy 기반
- bulk insert
- primary key 충돌 시 upsert 처리
