import re
import datetime

ALLOWED_TABLES = {
    "SAFE_ORDERS",
    "SAFE_CUSTOMERS",
    "SAFE_LOANS"
}

MAX_LIMIT = 500

def sql_validation_node(state: GraphState):
    query = state.get("sql_query", "").strip().upper()
    ts = datetime.datetime.utcnow().isoformat()

    if not query.startswith(("SELECT", "WITH")):
        return {"is_sql_safe": False, "logs": [f"[{ts}] SQL_DENY: Not read-only"]}

    forbidden = r"\b(DELETE|UPDATE|INSERT|DROP|ALTER|CREATE|EXEC|CALL)\b"
    if re.search(forbidden, query):
        return {"is_sql_safe": False, "logs": [f"[{ts}] SQL_DENY: Forbidden keyword"]}

    # LIMIT zorunlu
    limit_match = re.search(r"LIMIT\s+(\d+)", query)
    if not limit_match:
        return {"is_sql_safe": False, "logs": [f"[{ts}] SQL_DENY: LIMIT required"]}

    if int(limit_match.group(1)) > MAX_LIMIT:
        return {"is_sql_safe": False, "logs": [f"[{ts}] SQL_DENY: LIMIT too large"]}

    # Table whitelist
    tables = re.findall(r"FROM\s+([A-Z_]+)", query)
    for t in tables:
        if t not in ALLOWED_TABLES:
            return {"is_sql_safe": False, "logs": [f"[{ts}] SQL_DENY: Table {t} not allowed"]}

    return {
        "is_sql_safe": True,
        "logs": [f"[{ts}] SQL_OK: Query validated"]
    }


workflow.add_node("sql_validation", sql_validation_node)
