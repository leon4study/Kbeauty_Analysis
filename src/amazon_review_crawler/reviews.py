"""
File: src/amazon_review_crawler/reviews.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
무엇인가 (What)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Amazon ``reviews`` 테이블 스키마 정의 + 적재 함수.
items.py 와 동일 패턴 — ``load_reviews()`` 한 번에 스키마 보장 + 적재.

왜 있는가 (Why)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 리뷰 스키마를 별도 파일로 분리해 items 스키마와 충돌 없이 독립 관리.
- 크롤러(main.py) 는 ``load_reviews(df, client)`` 만 호출 — SQL 세부사항 모름.

어디에 쓰이는가 (Where)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- ``src/amazon_review_crawler/main.py`` 크롤링 루프에서 items 적재 직후 호출.

테이블 스키마 요약
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    reviews (PK: review_num)
      review_num    리뷰 고유 ID
      ASIN          상품 ID (items.ASIN 참조 — FK 미설정, 앱 레벨 보장)
      customer_id   리뷰 작성자 ID
      customer_name 리뷰 작성자 이름
      title         리뷰 제목
      date          수집 원문 날짜 문자열
      review_rating 별점 (텍스트 — "5.0 out of 5 stars" 형태)
      content       리뷰 본문

미구현 / 설계 노트
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- ASIN 컬럼에 인덱스 없음. 현재 규모(수천 rows)에서는 문제없으나,
  "특정 ASIN 의 전체 리뷰" 쿼리를 MySQL 에서 직접 날릴 일이 생기면
  ``CREATE INDEX idx_reviews_asin ON reviews(ASIN)`` 추가 권장.
- review_rating 은 텍스트로 저장 — 숫자 변환은 노트북 전처리 단계에서 수행.

관련 파일 (Related)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- src/amazon_review_crawler/mysql.py    ← 실제 SQL 실행
- src/amazon_review_crawler/items.py   ← 동일 패턴의 items 테이블 적재
- src/amazon_review_crawler/main.py    ← 호출부
- docs/db_schema.md                    ← 전체 DB 스키마 문서
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