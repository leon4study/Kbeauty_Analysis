"""
File: src/amazon_review_crawler/items.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
무엇인가 (What)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Amazon ``items`` 테이블 스키마 정의 + 적재 함수.
``load_items()`` 한 번 호출로 스키마 보장(없으면 생성) 후 DataFrame 을
upsert / insert 중 하나로 MySQL 에 올린다.

왜 있는가 (Why)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 스키마와 적재 로직을 한 파일에 두면, 컬럼 추가 시 스키마·적재·호출부를
  한 곳만 보면 됨.
- ``mysql.MySqlClient`` 가 실제 SQL 실행을 담당하고, 이 파일은 *어떤 테이블에
  어떤 컬럼을 넣는지* 만 정의 — 단일 책임.
- reviews.py 와 동일 패턴 → 새 테이블 추가 시 파일 복사 후 스키마만 교체.

어디에 쓰이는가 (Where)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- ``src/amazon_review_crawler/main.py`` 의 크롤링 루프 끝에서 호출.
  배치(5 브랜드) 크롤링이 끝날 때마다 ``load_items(df, client)`` 한 번씩.

테이블 스키마 요약
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    items (PK: ASIN)
      ASIN          상품 고유 ID (Amazon Standard Identification Number)
      title         상품명
      order         크롤링 수집 순서
      category      Amazon 대분류
      brand         브랜드명
      price         가격 (USD)
      global_rating_count  글로벌 평점 수
      description   상품 상세 설명 (JSON)
      Special_Feature  특수 기능 태그
      total_star_mean  평균 별점
      detail_dict   상세 스펙 (JSON)
      best_sellers_rank_Feature  베스트셀러 순위 텍스트
      Ingredients   성분 목록
      is_bundle     번들 상품 여부

관련 파일 (Related)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- src/amazon_review_crawler/mysql.py    ← bulk_upsert / bulk_insert_ignore 구현
- src/amazon_review_crawler/reviews.py ← 동일 패턴의 reviews 테이블 적재
- src/amazon_review_crawler/main.py    ← 호출부
- docs/db_schema.md                    ← 전체 DB 스키마 문서
"""
from __future__ import annotations

import pandas as pd
from sqlalchemy import (
    JSON,
    BOOLEAN,
    INTEGER,
    Column,
    Float,
    MetaData,
    String,
    Table,
    Text,
)

from mysql import MySqlClient


def load_items(
    df: pd.DataFrame,
    my_sql_client: MySqlClient,
    method: str = "upsert",
) -> None:
    """크롤링한 Amazon items DataFrame을 MySQL ``items`` 테이블에 적재.

    스키마는 함수 안에서 ``MetaData`` + ``Table`` 로 정의하고 (없으면 자동 생성),
    적재 방식은 ``method`` 인자로 분기한다.

    Args:
        df: 크롤링 결과 DataFrame. 컬럼명이 아래 ``Table`` 정의와 일치해야 함.
        my_sql_client: 적재할 ``MySqlClient`` 인스턴스.
        method: 적재 방식.

            - ``"upsert"`` (기본): PK(``ASIN``) 충돌 시 새 값으로 update,
              충돌 없으면 INSERT. 같은 상품을 다시 크롤링했을 때 가격/평점/설명 등을
              **최신값으로 갱신**하고 싶을 때.
            - ``"insert"``: PK 충돌 시 새 row를 **무시**하고 기존 row 보존.
              "이미 있는 ASIN은 그대로, 신규 ASIN만 추가" 시맨틱.

    Raises:
        ValueError: ``method`` 가 위 두 값이 아닐 때.
    """
    metadata = MetaData()
    table = Table(
        "items",
        metadata,
        Column("ASIN", String(13), primary_key=True),
        Column("title", Text, nullable=False),
        Column("order", INTEGER, nullable=False),
        Column("category", Text, nullable=True),
        Column("brand", Text, nullable=False),
        Column("price", Float, nullable=True),
        Column("global_rating_count", String(11), nullable=True),
        Column("description", JSON, nullable=True),
        Column("Special_Feature", Text, nullable=True),
        Column("total_star_mean", Float, nullable=True),
        Column("detail_dict", JSON, nullable=True),
        Column("best_sellers_rank_Feature", Text, nullable=True),
        Column("Ingredients", Text, nullable=True),
        Column("is_bundle", BOOLEAN, nullable=True),
    )
    # 적재 전에 스키마 보장 (없으면 생성).
    my_sql_client.create_table(metadata)

    if method == "upsert":
        my_sql_client.bulk_upsert(table=table, df=df)
    elif method == "insert":
        my_sql_client.bulk_insert_ignore(table=table, df=df)
    else:
        raise ValueError(
            f"method must be 'upsert' or 'insert', got {method!r}"
        )