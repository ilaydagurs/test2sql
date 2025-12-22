# src/text2sql/nodes/policy.py
from __future__ import annotations
import re
from text2sql.orchestrator.state import OrchestratorState

_PII_HINTS = re.compile(r"\b(tc|tckn|kimlik|iban|adres|telefon|email|e-?posta)\b", re.IGNORECASE)

def policy_node(state: OrchestratorState) -> OrchestratorState:
    role = (state.get("user_role") or "").lower()
    msg = (state.get("user_message") or "")

    # default allow
    state["allowed"] = True
    state["policy_reason"] = ""

    # Example: teller cannot ask PII
    if role == "teller" and _PII_HINTS.search(msg):
        state["allowed"] = False
        state["policy_reason"] = "Teller rolü PII içeren alanlara erişemez."
        return state

    # If router already decided REFUSE, keep it
    if state.get("intent") == "REFUSE":
        state["allowed"] = False
        state["policy_reason"] = state.get("policy_reason") or "Güvensiz/zararlı istek."
        return state

    return state
