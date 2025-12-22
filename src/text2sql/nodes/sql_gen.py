# src/text2sql/nodes/sql_gen.py
from __future__ import annotations
from text2sql.orchestrator.state import OrchestratorState

def sql_gen_node(state: OrchestratorState) -> OrchestratorState:
    msg = state.get("user_message", "")
    tables = state.get("table_candidates") or []
    cols = state.get("column_candidates") or []

    # TODO: replace with LLM prompt using tables/cols
    # Minimal heuristic: if "son 7" in message
    if "son 7" in msg.lower():
        state["sql"] = f"SELECT tarih, tutar FROM {tables[0]} WHERE tarih >= CURRENT_DATE - INTERVAL '7 days' LIMIT 200"
    else:
        state["sql"] = f"SELECT {', '.join(cols[:2])} FROM {tables[0]} LIMIT 200"
    return state
