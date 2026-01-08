import duckdb
import pandas as pd

def init_conn(db_path: str = ":memory:") -> duckdb.DuckDBPyConnection:
    return duckdb.connect(database=db_path)

def run_sql(conn: duckdb.DuckDBPyConnection, sql: str) -> pd.DataFrame:
    return conn.execute(sql).df()

def get_schema_overview(conn: duckdb.DuckDBPyConnection, schema_name: str = "bank") -> pd.DataFrame:
    """
    Returns a small overview of tables/views in a schema, including column counts.
    Used by the Streamlit sidebar.
    """
    # List tables & views
    objects = conn.execute(
        """
        SELECT table_name, table_type
        FROM information_schema.tables
        WHERE table_schema = ?
        ORDER BY table_type, table_name
        """,
        [schema_name],
    ).df()

    if objects.empty:
        return objects

    # Column counts per object
    col_counts = conn.execute(
        """
        SELECT table_name, COUNT(*) AS column_count
        FROM information_schema.columns
        WHERE table_schema = ?
        GROUP BY table_name
        """,
        [schema_name],
    ).df()

    out = objects.merge(col_counts, on="table_name", how="left")
    out["column_count"] = out["column_count"].fillna(0).astype(int)
    return out
