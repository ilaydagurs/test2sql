from pathlib import Path
import json
import duckdb

REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "data" / "duckdb" / "bank_txn_analytics.duckdb"
OUT_DIR = REPO_ROOT / "data" / "metadata"
SCHEMA = "bank"

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))

    tables = con.execute("""
        SELECT table_schema, table_name, table_type
        FROM information_schema.tables
        WHERE table_schema = ?
        ORDER BY table_name
    """, [SCHEMA]).fetchall()

    schema_json = {"schema": SCHEMA, "tables": []}
    allowlist = {"schema": SCHEMA, "tables": {}}

    for ts, tn, tt in tables:
        cols = con.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = ? AND table_name = ?
            ORDER BY ordinal_position
        """, [ts, tn]).fetchall()

        row_count = None
        if tt.upper() == "BASE TABLE":
            row_count = con.execute(f"SELECT COUNT(*) FROM {ts}.{tn}").fetchone()[0]

        fq = f"{ts}.{tn}"
        schema_json["tables"].append({
            "table": fq,
            "type": tt,
            "row_count": row_count,
            "columns": [{"name": c, "type": t} for c, t in cols]
        })
        allowlist["tables"][fq] = [c for c, _ in cols]

    con.close()

    (OUT_DIR / "schema.json").write_text(json.dumps(schema_json, indent=2), encoding="utf-8")
    (OUT_DIR / "allowlist.json").write_text(json.dumps(allowlist, indent=2), encoding="utf-8")
    print("OK: wrote data/metadata/schema.json and data/metadata/allowlist.json")

if __name__ == "__main__":
    main()
