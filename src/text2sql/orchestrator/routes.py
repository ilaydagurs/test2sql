# src/text2sql/orchestrator/routes.py
from __future__ import annotations
from text2sql.orchestrator.state import OrchestratorState


def route_from_router(state: OrchestratorState) -> str:
    intent = state.get("intent")
    conf = float(state.get("confidence", 0.0))
    needs = bool(state.get("needs_clarification", False))

    if intent in ["REFUSE"]:
        return "refuse"
    if needs or conf < 0.6 or intent == "CLARIFY":
        return "clarify"
    return "policy"


def route_after_policy(state: OrchestratorState) -> str:
    if not state.get("allowed", True):
        return "refuse"
    intent = state.get("intent")
    if intent == "ASK_METADATA":
        return "metadata"
    # EXECUTE_SQL / GENERATE_SQL both need validation, but GENERATE_SQL needs metadata first
    if intent == "EXECUTE_SQL":
        return "validate"
    if intent == "GENERATE_SQL":
        return "metadata"
    return "answer"


def route_after_metadata(state: OrchestratorState) -> str:
    intent = state.get("intent")
    if intent == "ASK_METADATA":
        return "answer"
    return "sql_gen"


def route_after_validate(state: OrchestratorState) -> str:
    return "execute" if state.get("sql_ok", False) else "answer"
