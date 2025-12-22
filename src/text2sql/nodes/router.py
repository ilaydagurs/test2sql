# src/text2sql/nodes/router.py
from __future__ import annotations
import re
from typing import Any, Dict
from text2sql.orchestrator.state import OrchestratorState, Intent

_DANGEROUS_SQL = re.compile(r"\b(drop|delete|update|insert|alter|truncate)\b", re.IGNORECASE)
_SELECT_START = re.compile(r"^\s*select\b", re.IGNORECASE)

def _has_sql(text: str) -> bool:
    return bool(_SELECT_START.search(text.strip()))

def _is_dangerous(text: str) -> bool:
    return bool(_DANGEROUS_SQL.search(text))

def router_node(state: OrchestratorState) -> OrchestratorState:
    msg = (state.get("user_message") or "").strip()
    provided_sql = (state.get("provided_sql") or "").strip()

    # default router outputs
    state["entities"] = state.get("entities", {})
    state["confidence"] = 0.75
    state["needs_clarification"] = False
    state["clarify_question"] = ""

    # 1) explicit provided_sql has priority
    if provided_sql:
        if _is_dangerous(provided_sql):
            state["intent"] = "REFUSE"
            state["confidence"] = 0.99
            return state
        state["intent"] = "EXECUTE_SQL"
        return state

    # 2) user pasted SQL in message
    if _has_sql(msg):
        if _is_dangerous(msg):
            state["intent"] = "REFUSE"
            state["confidence"] = 0.99
            return state
        state["intent"] = "EXECUTE_SQL"
        state["provided_sql"] = msg
        return state

    # 3) refuse patterns (DROP/DELETE request intent)
    if _is_dangerous(msg):
        state["intent"] = "REFUSE"
        state["confidence"] = 0.95
        return state

    # 4) metadata questions
    meta_keywords = ["hangi tablo", "tablolar", "kolon", "schema", "şema", "alan", "column", "table"]
    if any(k in msg.lower() for k in meta_keywords):
        state["intent"] = "ASK_METADATA"
        state["confidence"] = 0.8
        return state

    # 5) very short / ambiguous => clarify
    if len(msg) < 3 or msg in ["?", "؟؟", "…"]:
        state["intent"] = "CLARIFY"
        state["confidence"] = 0.4
        state["needs_clarification"] = True
        state["clarify_question"] = "Ne sorgulamak istiyorsun? (örn: zaman aralığı, metrik, filtre)"
        return state

    # 6) default: generate sql
    state["intent"] = "GENERATE_SQL"
    state["confidence"] = 0.7
    return state
