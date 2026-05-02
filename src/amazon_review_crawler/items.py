"""Amazon items 데이터를 MySQL ``items`` 테이블에 적재.

스키마 정의 + 적재 메서드 분기 wrapper. 실제 SQL은 ``mysql.MySqlClient`` 위임.
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