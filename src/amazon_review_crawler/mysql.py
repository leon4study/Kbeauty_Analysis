"""Kbeauty Amazon 크롤러용 MySQL 클라이언트.

설계 가정:
- 단일 머신, 단일 사용자, 주 1회 배치 잡 (분산 크롤링 X, 라이브 consumer X)
- DB는 잡 시작할 때 사람이 켜고 끝나면 끄는 패턴 (24/7 X)
- 한 잡 안에서 DB가 잠깐 끊기는 정도(네트워크 블립, deadlock 등)는 흡수

주요 기능:
- master / 옵셔널 replica 분리 (env에 ``DB_REPLICA_URL`` 있을 때만 replica 활성화)
- ``pool_pre_ping=True`` 로 좀비 connection 자동 회복
- 가벼운 ``_retry`` (3회 백오프) — transient 오류 흡수
- 적재는 bulk 위주: ``bulk_upsert`` / ``bulk_insert_ignore``
  (옛 "CSV로 dump → ASIN 중복 체크" 워크어라운드를 SQL idiom 하나로 대체)
- preflight ping: 시작 시 DB 연결 즉시 검증 (긴 잡 직전에 fail-fast)
- ``dispose()`` 로 명시적 자원 정리

확장 힌트 (필요해지면):
- 분산 크롤러 / 같은 잡 동시 실행 방지 → MySQL ``GET_LOCK(name, timeout)``
- 라이브 consumer + 전체 reload → staging 테이블 + ``RENAME TABLE`` 원자 swap
  (둘 다 구현 예시: ``~/GitStudy/utils/db_patterns/mysql_production_attempt.py``)
"""
from __future__ import annotations

import time
from typing import Optional

import pandas as pd
from sqlalchemy import MetaData, Table, create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError


class MySqlClient:
    """SQLAlchemy 기반 MySQL 클라이언트.

    Args:
        master_url: 쓰기/읽기 둘 다 가능한 master DB URL.
            형식: ``mysql+mysqlconnector://user:password@host:port/database``
        replica_url: 읽기 전용 replica DB URL. ``None`` 이면 read도 master로.
        pool_size: connection pool 기본 크기. 단일 워커엔 2면 충분.
        max_overflow: pool 가득 찼을 때 허용할 추가 connection.

    Raises:
        OperationalError: 시작 시 preflight (``SELECT 1``) 실패 — DB가 꺼져있거나
            자격증명/URL 오류. 긴 잡 시작 전에 명확히 fail.
    """

    def __init__(
        self,
        master_url: str,
        replica_url: Optional[str] = None,
        pool_size: int = 2,
        max_overflow: int = 2,
    ):
        # pool_pre_ping: connection 사용 직전에 ping → 좀비/끊긴 연결 자동 재연결.
        # pool_recycle: MySQL ``wait_timeout`` (기본 8시간) 만료 전에 connection 새로고침.
        engine_kw = dict(
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        self.engine_master: Engine = create_engine(master_url, **engine_kw)
        self.engine_replica: Optional[Engine] = (
            create_engine(replica_url, **engine_kw) if replica_url else None
        )
        self._preflight()

    # ------------------------------------------------------------------
    # 내부 헬퍼
    # ------------------------------------------------------------------
    def _preflight(self) -> None:
        """시작 시 master에 ``SELECT 1`` 으로 즉시 연결 검증.

        긴 크롤링 잡을 시작했는데 처음부터 DB가 꺼져있어 끝까지 실패하는
        사고를 방지. 실패하면 사람이 알아보기 좋은 메시지로 raise.
        """
        try:
            with self.engine_master.connect() as conn:
                conn.execute(text("SELECT 1"))
        except OperationalError as e:
            raise OperationalError(
                "MySQL master 연결 실패. MySQL 서비스 켜져있는지 확인 "
                "('brew services start mysql' 또는 'mysql.server start').",
                e.params,
                e.orig,
            ) from e

    def _retry(
        self,
        func,
        retries: int = 3,
        backoff: float = 1.0,
        exceptions: tuple = (OperationalError,),
    ):
        """transient 오류를 지수 백오프로 재시도하는 래퍼.

        ``OperationalError`` 같은 일시적 오류(네트워크 블립, deadlock retry 권고 등)는
        잡 전체를 죽이지 말고 ``backoff * 2^attempt`` 초씩 기다리다 다시 시도한다.
        ``retries`` 횟수 다 실패하면 마지막 예외를 그대로 raise.

        Args:
            func: 인자 없이 호출 가능한 callable. 재시도할 단위 작업을 감싸 호출.
            retries: 총 시도 횟수.
            backoff: 첫 sleep(초). 매 재시도마다 2배.
            exceptions: 재시도 대상으로 잡을 예외 타입.
        """
        last_exc: Optional[BaseException] = None
        for attempt in range(retries):
            try:
                return func()
            except exceptions as e:
                last_exc = e
                if attempt < retries - 1:
                    time.sleep(backoff * (2 ** attempt))
        assert last_exc is not None  # 도달 가능한 유일 경로는 retries 다 실패한 케이스
        raise last_exc

    # ------------------------------------------------------------------
    # 읽기 — replica 우선, 없으면 master
    # ------------------------------------------------------------------
    def fetch_as_dataframe(
        self,
        query: str,
        params: Optional[dict] = None,
        use_replica: bool = True,
        chunksize: Optional[int] = None,
    ) -> pd.DataFrame:
        """SELECT 쿼리 결과를 DataFrame으로 반환.

        Args:
            query: 실행할 SQL.
            params: bind 파라미터 (SQL injection 방지). 예:
                ``query="SELECT * FROM items WHERE brand=:b"``, ``params={"b": "cosrx"}``.
            use_replica: True + replica 있으면 replica 사용. replica 없으면 자동 master fallback.
                ⚠️ replica는 replication lag 있을 수 있으니 "방금 쓴 row 즉시 읽기"엔 부적합.
            chunksize: 큰 결과셋을 한 번에 로드 안 하고 chunk DataFrame iterator로.
                ``None`` 이면 전체를 한 번에 로드.
        """
        engine = (
            self.engine_replica
            if (use_replica and self.engine_replica)
            else self.engine_master
        )

        def _do():
            with engine.connect() as conn:
                return pd.read_sql(text(query), conn, params=params, chunksize=chunksize)

        return self._retry(_do)

    # ------------------------------------------------------------------
    # 쓰기 — bulk 위주
    # ------------------------------------------------------------------
    def bulk_upsert(
        self, table: Table, df: pd.DataFrame, chunk_size: int = 1000
    ) -> None:
        """``INSERT ... ON DUPLICATE KEY UPDATE`` 로 bulk upsert.

        Primary key (또는 UNIQUE) 충돌 시 기존 row를 새 값으로 **update**,
        충돌 없으면 새 row **INSERT**. 옛 "CSV에 dump 후 ASIN 중복 체크" 워크어라운드를
        SQL idiom 한 번으로 대체.

        Args:
            table: SQLAlchemy ``Table`` — 컬럼 정의 + primary key 정보 사용.
            df: 적재할 DataFrame. 컬럼명이 table 컬럼과 일치해야 함.
            chunk_size: ``executemany`` batch 크기. 너무 크면 MySQL ``max_allowed_packet`` 초과,
                너무 작으면 라운드트립 오버헤드. 1000이 보통 sweet spot.
        """
        if df.empty:
            return
        rows = df.to_dict(orient="records")
        cols = list(rows[0].keys())
        col_sql = ", ".join(f"`{c}`" for c in cols)
        placeholders = ", ".join(f":{c}" for c in cols)
        # PK 컬럼은 UPDATE 절에서 제외 (PK를 자기 자신으로 update해봤자 의미 없음).
        pk_cols = {c.name for c in table.primary_key.columns}
        update_cols = [c for c in cols if c not in pk_cols]
        if not update_cols:
            # 컬럼이 전부 PK인 케이스 → INSERT IGNORE와 시맨틱 동일
            return self.bulk_insert_ignore(table, df, chunk_size)
        update_sql = ", ".join(f"`{c}`=VALUES(`{c}`)" for c in update_cols)

        sql = (
            f"INSERT INTO `{table.name}` ({col_sql}) VALUES ({placeholders}) "
            f"ON DUPLICATE KEY UPDATE {update_sql}"
        )

        def _do():
            with self.engine_master.begin() as conn:
                for i in range(0, len(rows), chunk_size):
                    conn.execute(text(sql), rows[i : i + chunk_size])

        self._retry(_do)

    def bulk_insert_ignore(
        self, table: Table, df: pd.DataFrame, chunk_size: int = 1000
    ) -> None:
        """``INSERT IGNORE`` 로 bulk insert (충돌 시 그냥 skip).

        PK/UNIQUE 충돌하는 row는 **무시**하고 넘어감 (기존 값 유지). 시맨틱:
        "이미 있으면 그대로 두고 새것만 추가". 예: 크롤러가 같은 ASIN을 다시
        가져와도 기존 row를 덮지 않고 그대로 두고 싶을 때.

        Args:
            table: SQLAlchemy ``Table``.
            df: 적재할 DataFrame.
            chunk_size: ``executemany`` batch 크기.
        """
        if df.empty:
            return
        rows = df.to_dict(orient="records")
        cols = list(rows[0].keys())
        col_sql = ", ".join(f"`{c}`" for c in cols)
        placeholders = ", ".join(f":{c}" for c in cols)

        sql = f"INSERT IGNORE INTO `{table.name}` ({col_sql}) VALUES ({placeholders})"

        def _do():
            with self.engine_master.begin() as conn:
                for i in range(0, len(rows), chunk_size):
                    conn.execute(text(sql), rows[i : i + chunk_size])

        self._retry(_do)

    # ------------------------------------------------------------------
    # 스키마
    # ------------------------------------------------------------------
    def create_table(self, metadata: MetaData) -> None:
        """``metadata`` 안 모든 테이블을 master에 생성 (이미 있으면 무시)."""
        metadata.create_all(self.engine_master)

    def drop_table(self, table: Table) -> None:
        """단일 테이블 ``DROP`` (없으면 조용히 무시).

        ⚠️ 데이터 손실. 테스트/리셋 외 신중히 사용.
        """
        with self.engine_master.begin() as conn:
            conn.execute(text(f"DROP TABLE IF EXISTS `{table.name}`"))

    # ------------------------------------------------------------------
    # 정리
    # ------------------------------------------------------------------
    def dispose(self) -> None:
        """connection pool 명시적 정리.

        잡 끝날 때 호출 권장. (Python GC가 결국 처리하지만, 명시적이 더 안전.)
        """
        self.engine_master.dispose()
        if self.engine_replica:
            self.engine_replica.dispose()