# src/text2sql/nodes/sql_validate.py
from __future__ import annotations
import re
from text2sql.orchestrator.state import OrchestratorState

_DANGEROUS = re.compile(r"\b(drop|delete|update|insert|alter|truncate)\b", re.IGNORECASE)
_MULTI_STATEMENT = re.compile(r";\s*\S+", re.IGNORECASE)
_SELECT_START = re.compile(r"^\s*select\b", re.IGNORECASE)
_HAS_LIMIT = re.compile(r"\blimit\b", re.IGNORECASE)

DEFAULT_LIMIT = 200

def sql_validate_node(state: OrchestratorState) -> OrchestratorState:
    sql = (state.get("sql") or "").strip()
    issues = []

    state["sql_ok"] = True
    state["sql_issues"] = []

    if not sql:
        state["sql_ok"] = False
        state["sql_issues"] = ["SQL missing"]
        return state

    # hard blocks
    if not _SELECT_START.search(sql):
        issues.append("Only SELECT statements are allowed.")
    if _DANGEROUS.search(sql):
        issues.append("Dangerous SQL operation detected.")
    if _MULTI_STATEMENT.search(sql):
        issues.append("Multiple statements detected; only single statement allowed.")

    # allowlist check (soft/hard - choose hard for now)
    tables = state.get("table_candidates") or []
    cols = state.get("column_candidates") or []
    if tables:
        if not any(re.search(rf"\b{re.escape(t)}\b", sql, re.IGNORECASE) for t in tables):
            issues.append("SQL does not reference allowed tables from metadata.")

    if issues:
        state["sql_ok"] = False
        state["sql_issues"] = issues
        return state

    # soft: enforce LIMIT
    if not _HAS_LIMIT.search(sql):
        state["sql"] = f"{sql.rstrip(';')} LIMIT {DEFAULT_LIMIT}"
        state["sql_issues"] = ["LIMIT added for safety/performance."]

    return state
