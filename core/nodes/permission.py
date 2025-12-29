from core.logging import log

def check_intent_permission(state):
    if state["user_role"] not in ("admin", "analyst"):
        return {**state, "sql_error": "Unauthorized", **log("Permission denied")}
    return {**state, **log("Permission granted")}