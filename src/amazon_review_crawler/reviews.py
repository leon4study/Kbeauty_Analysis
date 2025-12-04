from mysql1 import MySqlClient
import pandas as pd
from sqlalchemy import MetaData, Column, String, DateTime,Integer,Float, Table, Text

def load_reviews(
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
    if method == "insert":
        my_sql_client.insert(df=df, table=table, metadata=metadata)
    elif method == "upsert":
        my_sql_client.upsert(df=df, table=table, metadata=metadata)
    elif method == "overwrite":
        my_sql_client.overwrite(df=df, table=table, metadata=metadata)
    else:
        raise Exception("올바른 method를 설정해주세요: [insert, upsert, overwrite]")
