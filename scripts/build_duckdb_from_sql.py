from __future__ import annotations

import re
from pathlib import Path
import duckdb

REPO_ROOT = Path(__file__).resolve().parents[1]

SQL_DIR = REPO_ROOT / "data" / "raw" / "bank_txn_analytics_sql"
SQL_CREATE = SQL_DIR / "Create_Tables.sql"
SQL_INSERT = SQL_DIR / "Insert_Table.sql"

OUT_DB = REPO_ROOT / "data" / "duckdb" / "bank_txn_analytics.duckdb"
SCHEMA = "bank"

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore").replace("\ufeff", "")

def normalize_sql(sql: str) -> str:
    # Remove SQL Server-ish inline FK syntax like: CustomerID INT FOREIGN KEY REFERENCES Customers_Bank(CustomerID)
    sql = re.sub(
        r"\bINT\s+FOREIGN\s+KEY\s+REFERENCES\s+\w+\s*\(\s*\w+\s*\)",
        "INT",
        sql,
        flags=re.IGNORECASE,
    )

    # Prefix CREATE TABLE and INSERT INTO with schema
    sql = re.sub(r"(?im)^\s*CREATE\s+TABLE\s+(\w+)\s*\(",
                 rf"CREATE TABLE {SCHEMA}.\1 (", sql)
    sql = re.sub(r"(?im)^\s*INSERT\s+INTO\s+(\w+)\b",
                 rf"INSERT INTO {SCHEMA}.\1", sql)

    return sql

def split_statements(sql: str) -> list[str]:
    # split on semicolons
    parts = [s.strip() for s in sql.split(";")]
    return [p for p in parts if p]

def main() -> None:
    if not SQL_CREATE.exists():
        raise FileNotFoundError(f"Missing: {SQL_CREATE}")
    if not SQL_INSERT.exists():
        raise FileNotFoundError(f"Missing: {SQL_INSERT}")

    OUT_DB.parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(OUT_DB))
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA};")

    # Rebuild: drop tables if present (ignore errors)
    for t in ["Transactions_Bank", "Merchants_Master", "Cards_Master", "Customers_Bank"]:
        con.execute(f"DROP TABLE IF EXISTS {SCHEMA}.{t};")

    create_sql = normalize_sql(read_text(SQL_CREATE))
    insert_sql = normalize_sql(read_text(SQL_INSERT))

    for stmt in split_statements(create_sql):
        con.execute(stmt)

    for stmt in split_statements(insert_sql):
        con.execute(stmt)

    # Optional: a join-friendly view for Text2SQL (only if all tables exist)
    con.execute(f"""
        CREATE OR REPLACE VIEW {SCHEMA}.v_transactions_enriched AS
        SELECT
            t.*,
            c.CustomerName,
            c.Gender,
            c.Age,
            c.City AS CustomerCity,
            cm.CardType,
            cm.IssuerBank,
            m.MerchantName,
            m.Category AS MerchantCategory,
            m.City AS MerchantCity
        FROM {SCHEMA}.Transactions_Bank t
        JOIN {SCHEMA}.Customers_Bank c ON t.CustomerID = c.CustomerID
        JOIN {SCHEMA}.Cards_Master cm ON t.CardID = cm.CardID
        JOIN {SCHEMA}.Merchants_Master m ON t.MerchantID = m.MerchantID;
    """)

    # Print validation
    tables = con.execute(f"""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = '{SCHEMA}'
        ORDER BY table_name
    """).fetchall()

    counts = {}
    for (tn,) in tables:
        if tn.startswith("v_"):
            continue
        try:
            counts[tn] = con.execute(f"SELECT COUNT(*) FROM {SCHEMA}.{tn}").fetchone()[0]
        except Exception:
            counts[tn] = None

    con.close()

    print("OK: built", OUT_DB)
    print("Tables:", [t[0] for t in tables])
    print("Row counts:", counts)
    print(f"View: {SCHEMA}.v_transactions_enriched")

if __name__ == "__main__":
    main()
