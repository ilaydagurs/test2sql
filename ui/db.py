import duckdb
import pandas as pd

def init_conn(db_path: str = ":memory:") -> duckdb.DuckDBPyConnection:
    return duckdb.connect(database=db_path)

def run_sql(conn: duckdb.DuckDBPyConnection, sql: str) -> pd.DataFrame:
    return conn.execute(sql).df()
