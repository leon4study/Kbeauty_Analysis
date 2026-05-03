# MySQL 클라이언트 정리

`src/amazon_review_crawler/` 안에 mysql 관련 변종이 5개 흩어져 있던 것을 단순한 단일 `mysql.py` 로 정리하고, 학습 가치 있는 prod-grade 패턴 시도는 별도로 보존.

## 배경 / 의도

Amazon 리뷰 크롤러가 결과를 MySQL 에 적재. 처음엔 단순 SQLAlchemy 클라이언트 (`mysql1.py`) 였으나, **DB 클라이언트 설계 학습** 차원에서 prod-grade 패턴 (master/replica, 락, 백오프 retry, atomic staging swap, bulk operations) 을 시도해본 흔적이 `mysql2_developed.py` + 그를 사용하는 `*_with_mysql2.py` 들로 남아있었다.

근데 사용자 자평: **"만드는 데 의의를 두는 거였음"**. 실제 프로젝트는 단일 머신/주 1회 배치/단일 사용자 규모라 prod 패턴 대부분이 오버킬.

## 시도된 변종

| Variant | lines | 시도한 패턴 | 사용처 | 평가 |
|---------|------:|------------|--------|------|
| `mysql1.py` | 162 | 단순 SQLAlchemy `create_engine` + insert/upsert/overwrite/fetch_as_dataframe. PK 충돌 처리는 `DELETE + INSERT` (atomicity X) | `main.py`, `items.py`, `reviews.py` | 옛 canonical, 단순하지만 transient 에러/스케일에 약함 |
| `mysql2_developed.py` | 184 | **master / 옵셔널 replica + connection pool 튜닝 + MySQL `GET_LOCK` 분산 락 + `_retry` 지수 백오프 + bulk_upsert (`INSERT ... ON DUPLICATE KEY UPDATE`) + `insert_ignore_duplicates` (`INSERT IGNORE`) + atomic staging swap (`RENAME TABLE`) + `dispose()` 자원 정리** | (코드 안 사용됨) | prod-grade 패턴 종합 시도. 일부 메서드는 미완성 (atomic swap 의 `df.to_sql(if_exists="replace")` 가 LIKE 로 만든 staging 스키마를 덮음) |
| `items_with_mysql2.py` | 50 | `mysql2_developed.MySqlClient` 사용 + SQLAlchemy ORM-style table 정의 (`autoload_with=engine_master`). 모듈 레벨에 `my_sql_client.engine_master` 참조하지만 그 변수가 정의 안 됨 → NameError | (사용처 없음) | **미완성** |
| `main_with_mysql2.py` | 799 | master/replica DSN 으로 MySqlClient 생성, `processed_flag` 컬럼으로 SQL 레벨 dedup. **하지만 `from mysql1 import MySqlClient` — import 가 옛 클라이언트** → 인터페이스 불일치로 깨짐 | (사용처 없음) | **마이그레이션 미완성** |
| `old_version_main.py` | 870 | 옛 main 버전 (브랜드 필터, 스폰서 필터, `crawl_amazon` 옵션 추가 등이 없는 단순 버전). 사용 함수: 9개 vs main.py 14개 | — | 진화 이전 단계, 단순 옛 버전 |

## 사용자의 옛 워크플로 (왜 mysql1 한계를 느꼈나)

DB 가 잡 도중에 끊기는 상황에 대응하기 위해:
```
크롤링 → DB.insert() 실패 → in-memory 데이터 날아감
워크어라운드: 결과를 CSV 로 dump → 나중에 ASIN 중복 체크 → 다시 insert
```
즉 **CSV 가 "DB 죽었을 때 임시 저장소"** 역할. mysql2_developed 의 `bulk_upsert` (`ON DUPLICATE KEY UPDATE`) + `_retry` 가 이걸 SQL idiom 으로 직접 대체할 수 있는 패턴이었지만, 적용은 안 했음.

## 최종 채택 + 이유

새 `src/amazon_review_crawler/mysql.py` 작성 — **현 프로젝트 규모 (단일 머신 / 주 1회 배치 / 단일 사용자) 에 맞는 단순 + 안정** 버전:

- ✅ **`pool_pre_ping=True` + `pool_recycle=3600`** — DB 잠깐 끊겼다 살아나는 경우 좀비 connection 자동 회복 (`mysql1` 에 없던 것)
- ✅ **가벼운 `_retry` (3회 백오프)** — transient OperationalError 흡수
- ✅ **`bulk_upsert` (`ON DUPLICATE KEY UPDATE`) + `bulk_insert_ignore` (`INSERT IGNORE`)** — 옛 CSV-based dedup 워크어라운드를 SQL idiom 한 번으로
- ✅ **`fetch_as_dataframe(query, params=, use_replica=, chunksize=)`** — bind params (SQL injection 방지), 옵셔널 replica 라우팅, chunksize stream
- ✅ **`_preflight()` (시작 시 `SELECT 1`)** — 긴 잡 시작 전에 DB 안 켜져있으면 친절한 에러로 즉시 fail
- ✅ **옵셔널 replica** — `CRAWLER_DB_REPLICA_URL` env 있을 때만 활성, 없으면 master로 fallback
- ✅ **`dispose()`** — 명시적 자원 정리

**제거** (오버킬):
- `GET_LOCK` (분산 락) — 단일 워커 환경엔 불필요
- atomic staging swap — incremental upsert 라 통째 reload 안 함
- 옛 row 단위 `upsert()` (DELETE + INSERT 패턴) — atomicity 약하고 비효율

**Docstring** 에 "확장 힌트" 섹션 — 미래에 분산화 / 라이브 consumer 생기면 어떤 패턴 추가할지 + 참조 위치 (`~/GitStudy/utils/db_patterns/`) 명시.

## 사용처 마이그레이션

| 파일 | 변경 |
|------|------|
| `items.py` / `reviews.py` | `insert / upsert / overwrite` 분기 → `bulk_insert_ignore / bulk_upsert` 두 옵션. 위험한 `overwrite` (DROP+INSERT) 제거 |
| `main.py` | `from mysql1 import` → `from mysql import`. MySqlClient 생성 시그니처 변경 (`server_name=, database_name=, ...` → `master_url=, replica_url=`). env vars `ID/PW/DB_*` → `CRAWLER_*` prefix 통일 |
| `.env` / `.env.example` | `CRAWLER_DB_REPLICA_URL` 옵셔널 필드 추가 |

## canonical 위치

```
src/amazon_review_crawler/
├── __init__.py
├── mysql.py        (단순 + bulk + retry + preflight, 확장 힌트 docstring)
├── main.py         (URL 기반 client 생성, CRAWLER_* env)
├── items.py        (bulk_upsert / bulk_insert_ignore)
├── reviews.py      (동일)
└── (그 외 reviewing 도구들)
```

## 학습 노트 보존 위치

```
~/GitStudy/utils/db_patterns/
├── README.md                       (학습 노트 설명)
├── mysql_production_attempt.py     (= 옛 mysql2_developed.py)
├── items_with_mysql2.py
└── main_with_mysql2.py
```

`old_version_main.py` 는 단순 진화 흔적이라 git history 만 남김.

## 학습 포인트

1. **YAGNI**: prod 패턴을 미리 만들어두는 건 학습엔 좋지만, 안 쓸 추상화는 코드만 무거워짐. 진짜 분산/라이브 컨슈머가 생긴 시점에 도입.
2. **단순화 우선순위**: `pool_pre_ping` + `_retry` + `bulk_upsert` 만 있어도 옛 워크플로 (CSV dump + dedup) 의 90% 가 SQL 한 줄로 대체 가능.
3. **Master/Replica 의 진짜 의미**: 같은 머신에 둘 다 띄우면 master 다운 시 replica 도 같이 죽음 — replica 의 가용성 가치는 **다른 머신** 에 있을 때만.
4. **Atomic staging swap**: 라이브 consumer + 통째 reload 일 때만 의미. incremental upsert 워크플로엔 불필요.
5. **`OperationalError` 의 분류**: 모든 transient 가 retry 로 회복되지 않음 (예: 자격증명 오류). retry 대상 예외를 명확히 (`exceptions=` 인자).
6. **확장 힌트는 docstring 에**: prod 패턴 학습한 사람이 "필요해지면 여기 추가" 라는 신호를 코드에 남겨두면, 나중에 실제 필요해진 사람이 빠르게 대응 가능.

## 관련 commits

- `43e21f5` — refactor(amazon_crawler): replace mysql1 with simpler bulk-oriented mysql client
- (이전) `6499e26` — refactor: bring mysql2 variants into canonical amazon_review_crawler (이 commit 이 mysql2 변종들을 amazon_review_crawler/ 로 모아둔 시점)