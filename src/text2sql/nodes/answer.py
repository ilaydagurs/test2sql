from __future__ import annotations
from text2sql.orchestrator.state import OrchestratorState


def answer_node(state: OrchestratorState) -> OrchestratorState:
    intent = state.get("intent", "")
    allowed = state.get("allowed", True)
    sql_ok = state.get("sql_ok", True)

    # If request not allowed by policy
    if not allowed:
        state["final_answer"] = f"İstek reddedildi: {state.get('policy_reason', '')}"
        return state

    # Clarification intent
    if intent == "CLARIFY":
        state["final_answer"] = state.get("clarify_question") or "Daha net yazar mısın?"
        return state

    # Ask metadata intent
    if intent == "ASK_METADATA":
        tables = state.get("table_candidates") or []
        cols = state.get("column_candidates") or []
        state["final_answer"] = f"Mevcut tablolar: {tables}. Örnek kolonlar: {cols}."
        return state

    # Execute or Generate SQL intents
    if intent in ["EXECUTE_SQL", "GENERATE_SQL"]:
        if not sql_ok:
            issues = state.get("sql_issues", [])
            state["final_answer"] = f"SQL doğrulanamadı: {issues}"
            return state
        result = state.get("result")
        state["final_answer"] = f"SQL çalıştırıldı. Sonuç özeti: {result}"
        return state

    # Refuse intent
    if intent == "REFUSE":
        state["final_answer"] = "Bu isteği güvenlik nedeniyle yerine getiremiyorum."
        return state

    # Fallback response
    state["final_answer"] = "Tam anlayamadım; biraz daha detay verir misin?"
    return state
