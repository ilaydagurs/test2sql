# src/text2sql/nodes/execute.py
from __future__ import annotations
from text2sql.orchestrator.state import OrchestratorState

def execute_node(state: OrchestratorState) -> OrchestratorState:
    sql = state.get("sql", "")
    # TODO: integrate real DB execution
    state["result"] = {"dummy": True, "sql": sql, "rows": []}
    return state
