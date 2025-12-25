from __future__ import annotations

import sys
from pathlib import Path
import duckdb

REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "data" / "duckdb" / "bank_txn_analytics.duckdb"

def run_query(con: duckdb.DuckDBPyConnection, name: str, sql: str, limit_preview: int = 10) -> None:
    print("\n" + "=" * 80)
    print(f"TEST: {name}")
    print("- SQL:")
    print(sql.strip())

    cur = con.execute(sql)
    cols = [d[0] for d in cur.description] if cur.description else []
    rows = cur.fetchmany(limit_preview)

    print(f"- Columns ({len(cols)}): {cols}")
    print(f"- Preview rows (up to {limit_preview}): {rows}")

def assert_exists(con: duckdb.DuckDBPyConnection, object_name: str) -> None:
    # object_name like: bank.v_transactions_enriched
    schema, name = object_name.split(".", 1)
    found = con.execute("""
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = ? AND table_name = ?
        LIMIT 1
    """, [schema, name]).fetchone()
    if not found:
        raise RuntimeError(f"Missing required object: {object_name}")

def main() -> int:
    if not DB_PATH.exists():
        print(f"ERROR: DB file not found: {DB_PATH}")
        return 2

    con = duckdb.connect(str(DB_PATH))

    # 1) Confirm objects exist
    required = [
        "bank.Customers_Bank",
        "bank.Cards_Master",
        "bank.Merchants_Master",
        "bank.Transactions_Bank",
        "bank.v_transactions_enriched",
    ]
    for obj in required:
        assert_exists(con, obj)

    # 2) Print table list (bank schema)
    print("Bank schema objects:")
    print(con.execute("""
        SELECT table_name, table_type
        FROM information_schema.tables
        WHERE table_schema='bank'
        ORDER BY table_name
    """).fetchall())

    # 3) Row counts (base tables)
    print("\nRow counts:")
    for t in ["Customers_Bank", "Cards_Master", "Merchants_Master", "Transactions_Bank"]:
        n = con.execute(f"SELECT COUNT(*) FROM bank.{t}").fetchone()[0]
        print(f"- bank.{t}: {n}")

    # 4) Describe enriched view (contract check)
    print("\nDescribe bank.v_transactions_enriched:")
    desc = con.execute("DESCRIBE bank.v_transactions_enriched").fetchall()
    print(desc)

    # 5) Run “dashboard style” smoke queries
    run_query(con, "Preview enriched view",
              "SELECT * FROM bank.v_transactions_enriched ORDER BY TransactionDate, TransactionID LIMIT 5;")

    run_query(con, "Top merchants by total spend",
              """
              SELECT MerchantName, SUM(Amount) AS total_spend
              FROM bank.v_transactions_enriched
              GROUP BY MerchantName
              ORDER BY total_spend DESC
              LIMIT 10;
              """)

    run_query(con, "Spend by merchant category",
              """
              SELECT MerchantCategory, SUM(Amount) AS total_spend, COUNT(*) AS txn_count
              FROM bank.v_transactions_enriched
              GROUP BY MerchantCategory
              ORDER BY total_spend DESC;
              """)

    run_query(con, "Payment mode distribution",
              """
              SELECT Mode, COUNT(*) AS txn_count, SUM(Amount) AS total_amount
              FROM bank.v_transactions_enriched
              GROUP BY Mode
              ORDER BY txn_count DESC;
              """)

    run_query(con, "Gender-wise spend",
              """
              SELECT Gender, SUM(Amount) AS total_spend, COUNT(*) AS txn_count
              FROM bank.v_transactions_enriched
              GROUP BY Gender
              ORDER BY total_spend DESC;
              """)

    run_query(con, "Age group-wise spend (bucketed)",
              """
              SELECT
                CASE
                  WHEN Age BETWEEN 18 AND 25 THEN '18-25'
                  WHEN Age BETWEEN 26 AND 35 THEN '26-35'
                  WHEN Age BETWEEN 36 AND 45 THEN '36-45'
                  WHEN Age BETWEEN 46 AND 60 THEN '46-60'
                  ELSE '60+'
                END AS age_group,
                SUM(Amount) AS total_spend,
                COUNT(*) AS txn_count
              FROM bank.v_transactions_enriched
              GROUP BY age_group
              ORDER BY total_spend DESC;
              """)

    run_query(con, "Potential suspicious transactions (high amount)",
              """
              SELECT TransactionID, TransactionDate, CustomerName, Amount, Mode, MerchantName, MerchantCategory, City
              FROM bank.v_transactions_enriched
              WHERE Amount >= 10000
              ORDER BY Amount DESC, TransactionDate DESC;
              """)

    con.close()
    print("\nOK: smoke test completed successfully.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
