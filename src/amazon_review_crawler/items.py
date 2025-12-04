from mysql1 import MySqlClient
import pandas as pd
from sqlalchemy import MetaData, Column, String,Float, Table, Text, JSON, INTEGER, BOOLEAN

def load_items(
    df: pd.DataFrame,
    my_sql_client: MySqlClient,
    method: str = "upsert",
) -> None:
    """
    변환된 아이템 데이터를 MySQL에 로드하는 함수.

    Parameters:
    - df (pd.DataFrame): 변환된 데이터
    - my_sql_client (MySqlClient): 데이터베이스 클라이언트
    - method (str, optional): 삽입 방법 ('insert', 'upsert', 'overwrite')
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

    if method == "insert":
        my_sql_client.insert(df=df, table=table, metadata=metadata)
    elif method == "upsert":
        my_sql_client.upsert(df=df, table=table, metadata=metadata)
    elif method == "overwrite":
        my_sql_client.overwrite(df=df, table=table, metadata=metadata)
    else:
        raise Exception("올바른 method를 설정해주세요: [insert, upsert, overwrite]")
