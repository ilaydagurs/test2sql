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


from langgraph.graph import StateGraph, START, END

workflow = StateGraph(GraphState)

workflow.add_node("access_control", access_control_node)
workflow.add_node("sql_validation", sql_validation_node)

workflow.add_node(
    "unauthorized_exit",
    lambda s: {"response": "403 Forbidden", "logs": ["SECURITY_EXIT"]}
)

workflow.add_node(
    "sql_rejected",
    lambda s: {"response": "Invalid SQL", "logs": ["SQL_EXIT"]}
)

workflow.add_node(
    "process_start",
    lambda s: {"response": "Authorized & SQL Safe"}
)

workflow.add_edge(START, "access_control")

workflow.add_conditional_edges(
    "access_control",
    lambda s: "process_start" if s["auth_status"] else "unauthorized_exit",
    {
        "process_start": "sql_validation",
        "unauthorized_exit": "unauthorized_exit"
    }
)

workflow.add_conditional_edges(
    "sql_validation",
    lambda s: "process_start" if s["is_sql_safe"] else "sql_rejected",
    {
        "process_start": "process_start",
        "sql_rejected": "sql_rejected"
    }
)

workflow.add_edge("unauthorized_exit", END)
workflow.add_edge("sql_rejected", END)
workflow.add_edge("process_start", END)

app = workflow.compile()

