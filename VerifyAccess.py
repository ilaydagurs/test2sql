from typing import TypedDict, List, Annotated, Optional
import operator
import datetime

class GraphState(TypedDict):
    user_id: str
    metadata: dict  # Beklenen: {"action": "...", "resource": "..."}
    auth_status: bool
    logs: Annotated[List[str], operator.add] 
    response: str

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
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    user_info = BANK_USERS.get(user_id)

    # Eğer kayıtlı olmayan bir kullanıcı erişmeye çalışırsa
    if not user_info:
        log_entry = f"[{timestamp}] SECURITY ALERT: Access attempt by unknown User ID: {user_id}."
        return {"auth_status": False, "logs": [log_entry]}
    
    user_role = user_info["role"]
    
    # Matristen ilgili role ait yetkileri alıyor
    allowed_actions = BANK_AUTH_MATRIX.get(user_role, {}).get(resource, [])
    
    is_authorized = action in allowed_actions
    
    # Logları kaydediyor ve yetkisi varsa True, yoksa False döndürüyor.
    if is_authorized:
        log_entry = f"[{timestamp}] SUCCESS: {user_role} ({user_id}) authorized for {action} on {resource}."
        return {
            "auth_status": True, 
            "logs": [log_entry]
        }
    else:
        log_entry = f"[{timestamp}] FAILURE: {user_role} ({user_id}) denied access for {action} on {resource}."
        return {
            "auth_status": False, 
            "logs": [log_entry]
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
