from sqlalchemy import create_engine, MetaData, Table, text
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import sessionmaker
import pandas as pd
import time
import logging
from typing import Optional, List, Dict

"""
“SQLAlchemy + MySQL 환경에서 저는 읽기/쓰기 엔진을 분리하고 
GET_LOCK 기반의 중복 방지, ON DUPLICATE KEY UPDATE 기반의 idempotent 업서트, 
트랜잭션을 chunk 단위로 최소화하는 설계를 적용했습니다. 
문제가 생기면 자동 retry와 로그로 추적해 원인을 개선합니다.”
"""


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class MySqlClient:
    def __init__(
        self,
        master_url: str,
        replica_url: Optional[str] = None,
        pool_size: int = 5,
        max_overflow: int = 10,
        connect_args: Optional[Dict] = None,
    ):
        """
        master_url: 쓰기용 DSN (mysql+mysqlconnector://user:pw@host/db)
        replica_url: 읽기 전용 복제본 DSN (선택)
        """
        self.engine_master = create_engine(
            master_url, pool_size=pool_size, max_overflow=max_overflow, connect_args=connect_args or {}
        )
        self.engine_replica = (
            create_engine(replica_url, pool_size=pool_size, max_overflow=max_overflow, connect_args=connect_args or {})
            if replica_url
            else None
        )
        self.Session = sessionmaker(bind=self.engine_master, expire_on_commit=False)

    # ----------------------------
    # Lock utilities (GET_LOCK / RELEASE_LOCK)
    # ----------------------------
    def acquire_lock(self, conn, lock_name: str, timeout: int = 0) -> bool:
        """GET_LOCK returns 1 on success, 0 on timeout, NULL on error"""
        res = conn.execute(text("SELECT GET_LOCK(:name, :timeout) AS got"), {"name": lock_name, "timeout": timeout})
        got = res.scalar()
        return bool(got)

    def release_lock(self, conn, lock_name: str) -> bool:
        res = conn.execute(text("SELECT RELEASE_LOCK(:name) AS rel"), {"name": lock_name})
        return bool(res.scalar())

    # ----------------------------
    # Helper: retry decorator (simple)
    # ----------------------------
    def _retry(self, func, retries=3, backoff=1.0, exceptions=(OperationalError,)):
        for attempt in range(retries):
            try:
                return func()
            except exceptions as e:
                logger.warning(f"Attempt {attempt+1}/{retries} failed: {e}")
                if attempt + 1 == retries:
                    raise
                time.sleep(backoff * (2 ** attempt))

    # ----------------------------
    # Fetch using read replica when available
    # ----------------------------
    def fetch_as_dataframe(self, query: str, use_replica: bool = True, params: Optional[dict] = None, chunksize: Optional[int] = None) -> pd.DataFrame:
        engine = self.engine_replica if (use_replica and self.engine_replica) else self.engine_master
        try:
            if chunksize:
                # returns iterator of DataFrame chunks
                return pd.read_sql(sql=text(query), con=engine, params=params, chunksize=chunksize)
            else:
                return pd.read_sql(sql=text(query), con=engine, params=params)
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise

    # ----------------------------
    # Bulk upsert using MySQL 'ON DUPLICATE KEY UPDATE' (idempotent)
    # ----------------------------
    def bulk_upsert(self, table: Table, rows: List[Dict], chunk_size: int = 1000, lock_name: Optional[str] = None):
        """
        rows: list of dict
        Uses INSERT ... ON DUPLICATE KEY UPDATE for idempotency.
        Acquires GET_LOCK if lock_name provided to avoid concurrent runs.
        """
        if not rows:
            return

        def _do_work():
            with self.engine_master.begin() as conn:  # transaction scope, short
                if lock_name:
                    if not self.acquire_lock(conn, lock_name, timeout=0):
                        raise RuntimeError("Could not acquire lock")

                # use dialect insert ... on duplicate key update
                stmt = mysql_insert(table).values(rows[0])  # template for columns
                update_cols = {c.name: stmt.inserted[c.name] for c in table.columns if not c.primary_key}
                stmt = stmt.on_duplicate_key_update(**update_cols)

                # chunked execution using executemany
                for i in range(0, len(rows), chunk_size):
                    chunk = rows[i : i + chunk_size]
                    conn.execute(stmt, chunk)

                if lock_name:
                    self.release_lock(conn, lock_name)

        # retry transient OperationalError (deadlocks, lock wait timeout)
        self._retry(_do_work, retries=3, backoff=1.0, exceptions=(OperationalError, SQLAlchemyError))

    # ----------------------------
    # Upsert from DataFrame (converts to dicts)
    # ----------------------------
    def upsert_from_df(self, table: Table, df: pd.DataFrame, chunk_size: int = 1000, lock_name: Optional[str] = None):
        rows = df.to_dict(orient="records")
        self.bulk_upsert(table=table, rows=rows, chunk_size=chunk_size, lock_name=lock_name)

    # ----------------------------
    # Insert-only (append new rows by using ON DUPLICATE KEY DO NOTHING pattern)
    # Alternative: use insert_ignore or check PK existence server-side
    # ----------------------------
    def insert_ignore_duplicates(self, table: Table, df: pd.DataFrame, chunk_size: int = 1000, lock_name: Optional[str] = None):
        if df.empty:
            return

        rows = df.to_dict(orient="records")

        def _do_work():
            with self.engine_master.begin() as conn:
                if lock_name and not self.acquire_lock(conn, lock_name, timeout=0):
                    raise RuntimeError("Could not acquire lock")
                # MySQL: INSERT IGNORE INTO ...  (SQLAlchemy core doesn't have insert_ignore, use text fallback)
                cols = list(rows[0].keys())
                col_sql = ", ".join([f"`{c}`" for c in cols])
                placeholders = ", ".join([f":{c}" for c in cols])
                sql = f"INSERT IGNORE INTO {table.schema+'.' if table.schema else ''}{table.name} ({col_sql}) VALUES ({placeholders})"
                for i in range(0, len(rows), chunk_size):
                    chunk = rows[i : i + chunk_size]
                    conn.execute(text(sql), chunk)
                if lock_name:
                    self.release_lock(conn, lock_name)

        self._retry(_do_work, retries=3, backoff=1.0, exceptions=(OperationalError, SQLAlchemyError))

    # ----------------------------
    # Overwrite safely: write to staging table then atomic rename
    # ----------------------------
    def overwrite_df_atomic(self, table: Table, df: pd.DataFrame, staging_suffix: str = "_stg"):
        """
        1) create staging table (same schema)
        2) insert data into staging
        3) rename staging -> target in a transaction (atomic swap)
        Note: requires privileges to rename/drop tables.
        """
        stg_name = f"{table.name}{staging_suffix}"
        # Create staging table SQL (simple approach: CREATE TABLE stg LIKE target)
        with self.engine_master.connect() as conn:
            conn.execute(text(f"CREATE TABLE IF NOT EXISTS {stg_name} LIKE {table.name}"))
            # load into staging
            df.to_sql(name=stg_name, con=conn, if_exists="replace", index=False)
            # atomic swap: RENAME TABLE stg TO tmp_old, target TO tmp2, then finalize
            # simpler: drop old and rename staging -> target (be careful with permissions)
            conn.execute(text(f"RENAME TABLE {table.name} TO {table.name}_old, {stg_name} TO {table.name}"))
            conn.execute(text(f"DROP TABLE IF EXISTS {table.name}_old"))

    # ----------------------------
    # Utility: close engines
    # ----------------------------
    def dispose(self):
        try:
            self.engine_master.dispose()
            if self.engine_replica:
                self.engine_replica.dispose()
        except Exception:
            pass
