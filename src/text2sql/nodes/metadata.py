# src/text2sql/nodes/metadata.py
from __future__ import annotations
from text2sql.orchestrator.state import OrchestratorState

def metadata_node(state: OrchestratorState) -> OrchestratorState:
    # TODO: team will replace with real retrieval
    state["table_candidates"] = state.get("table_candidates") or ["satislar", "musteriler"]
    state["column_candidates"] = state.get("column_candidates") or ["tarih", "tutar", "musteri_id"]
    return state
