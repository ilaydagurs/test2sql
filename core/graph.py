from langgraph.graph import StateGraph, END
from core.state import AgentState
from core.nodes.permission import check_intent_permission
from core.nodes.format_response import format_response

def build_graph():
    g = StateGraph(AgentState)
    g.add_node("check_permission", check_intent_permission)
    g.add_node("format", format_response)
    g.set_entry_point("check_permission")
    g.add_edge("check_permission", "format")
    g.add_edge("format", END)
    return g.compile()