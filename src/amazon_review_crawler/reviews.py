"""Amazon reviews 데이터를 MySQL ``reviews`` 테이블에 적재.

스키마 정의 + 적재 메서드 분기 wrapper. 실제 SQL은 ``mysql.MySqlClient`` 위임.
"""
from __future__ import annotations

import pandas as pd
from sqlalchemy import Column, MetaData, String, Table, Text

from mysql import MySqlClient


def load_reviews(
    df: pd.DataFrame,
    my_sql_client: MySqlClient,
    method: str = "upsert",
) -> None:
    """크롤링한 Amazon reviews DataFrame을 MySQL ``reviews`` 테이블에 적재.

    Args:
        df: 크롤링 결과 DataFrame. 컬럼명이 아래 ``Table`` 정의와 일치해야 함.
        my_sql_client: ``MySqlClient`` 인스턴스.
        method: 적재 방식.

            - ``"upsert"`` (기본): PK(``review_num``) 충돌 시 새 값으로 update.
              리뷰 본문이 수정됐거나 평점이 변경됐을 때 갱신.
            - ``"insert"``: PK 충돌 시 무시 — "이미 있는 리뷰 그대로 두고 신규만".

    Raises:
        ValueError: ``method`` 가 위 두 값이 아닐 때.
    """
    metadata = MetaData()
    table = Table(
        "reviews",
        metadata,
        Column("review_num", String(15), nullable=False, primary_key=True),
        Column("ASIN", String(13), nullable=False),
        Column("customer_id", String(17), nullable=False),
        Column("customer_name", Text, nullable=False),
        Column("title", Text, nullable=False),
        Column("date", Text, nullable=False),
        Column("review_rating", Text, nullable=True),
        Column("content", Text, nullable=True),
    )
    my_sql_client.create_table(metadata)

    if method == "upsert":
        my_sql_client.bulk_upsert(table=table, df=df)
    elif method == "insert":
        my_sql_client.bulk_insert_ignore(table=table, df=df)
    else:
        raise ValueError(
            f"method must be 'upsert' or 'insert', got {method!r}"
        )