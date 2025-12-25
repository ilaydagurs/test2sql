from typing import TypedDict, List, Optional, Annotated
import operator
import datetime

class GraphState(TypedDict, total=False):
    # Identity & Auth
    user_id: str
    user_role: str
    metadata: dict  # {action, resource}
    auth_status: bool

    # SQL
    sql_query: str
    is_sql_safe: bool

    # Context
    db_type: str
    schema_version: str

    # Output
    response: str

    # Observability
    logs: Annotated[List[str], operator.add]


# DB'ye taşınabilir, geçici banka çalışanı ve yetki matrisi
BANK_AUTH_MATRIX = {
    "GENERAL_MANAGER": {
        "financial_reports": ["view_all_branches", "export_summary"],
        "customer_data": ["view_aggregate_stats"],
        "audit_logs": ["view_system_logs"],
        "branch_performance": ["compare_all_branches"]
    },
    "DATA_ANALYST": {
        "financial_reports": ["view_raw_data", "run_analytics"],
        "customer_data": ["view_anonymized"],
        "loan_performance": ["view_risk_models", "read_trends"],
        "branch_performance": ["view_all_branches"]
    },
    "BRANCH_MANAGER": {
        "financial_reports": ["view_branch_only"],
        "customer_data": ["view_customer_details", "export_branch_list"],
        "loan_performance": ["view_branch_loans"],
        "staff_data": ["view_branch_staff_performance"]
    }
}

# ID ile isim ve rol eşleme
BANK_USERS = {
    "u_001": {"name": "Alice", "role": "GENERAL_MANAGER"},
    "u_002": {"name": "Bob", "role": "DATA_ANALYST"},
    "u_003": {"name": "Charlie", "role": "BRANCH_MANAGER"}
}

# Tool ya da ajansız, düz node. Hata şansı yok, daha güvenli.
def access_control_node(state: GraphState):
    user_id = state["user_id"]
    action = state["metadata"].get("action")
    resource = state["metadata"].get("resource")

    timestamp = datetime.datetime.utcnow().isoformat()
    user_info = BANK_USERS.get(user_id)

    if not user_info:
        return {
            "auth_status": False,
            "logs": [f"[{timestamp}] AUTH_FAIL: Unknown user {user_id}"]
        }

    role = user_info["role"]
    allowed_actions = BANK_AUTH_MATRIX.get(role, {}).get(resource, [])

    if action not in allowed_actions:
        return {
            "auth_status": False,
            "user_role": role,
            "logs": [f"[{timestamp}] AUTH_DENY: {role} cannot {action} on {resource}"]
        }

    return {
        "auth_status": True,
        "user_role": role,
        "logs": [f"[{timestamp}] AUTH_OK: {role} authorized"]
    }


# Devamındaki ilgili kısımlar diğer partlara göre güncellenecek.

from typing import Literal
from langgraph.graph import StateGraph, END, START

# Router, yetki kontrolünden sonraki akış
def auth_router(state: GraphState) -> Literal["unauthorized_exit", "long_process_start"]:
    """
    Bu fonksiyon bir düğüm (node) değil, bir karar mekanizmasıdır.
    Düğüm isimlerini string olarak döner.
    """
    if state["auth_status"]:
        return "process_start"
    else:
        return "unauthorized_exit"


workflow = StateGraph(GraphState)


workflow.add_node("access_control", access_control_node) # Önceki adımda yazdığımız node
workflow.add_node("unauthorized_exit", lambda state: {"response": "Access Denied: Unauthorized Action."})


workflow.add_node("process_start", lambda state: state) 


workflow.add_edge(START, "access_control")

workflow.add_conditional_edges(
    "access_control", 
    auth_router,
    {
        "process_start": "process_start", 
        "unauthorized_exit": "unauthorized_exit"
    }
)


workflow.add_edge("unauthorized_exit", END)

app = workflow.compile()
