import duckdb

DB = r"data/duckdb/bank_txn_analytics.duckdb"

con = duckdb.connect(DB)

print("Tables in schema bank:")
print(con.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'bank'
    ORDER BY table_name
""").fetchall())

print("\nCounts:")
for t in ["Customers_Bank","Cards_Master","Merchants_Master","Transactions_Bank"]:
    try:
        n = con.execute(f"SELECT COUNT(*) FROM bank.{t}").fetchone()[0]
        print(f"{t}: {n}")
    except Exception as e:
        print(f"{t}: ERROR -> {e}")

print("\nDescribe view:")
print(con.execute("DESCRIBE bank.v_transactions_enriched").fetchall())

con.close()
