from core.logging import log

def format_response(state):
    state["final_response"] = {
        "status": "error" if state.get("sql_error") else "success",
        "answer": state.get("sql_error") or "OK",
        "logs": state["logs"]
    }
    return {**state, **log("Response formatted")}