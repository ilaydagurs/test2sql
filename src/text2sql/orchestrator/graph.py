from __future__ import annotations
from langgraph.graph import StateGraph, END

from text2sql.orchestrator.state import OrchestratorState
from text2sql.orchestrator.routes import (
    route_from_router, route_after_policy, route_after_metadata, route_after_validate
)
from text2sql.nodes.router import router_node
from text2sql.nodes.policy import policy_node
from text2sql.nodes.metadata import metadata_node
from text2sql.nodes.sql_gen import sql_gen_node
from text2sql.nodes.sql_validate import sql_validate_node
from text2sql.nodes.execute import execute_node
from text2sql.nodes.answer import answer_node


def build_app():
    g = StateGraph(OrchestratorState)

    g.add_node("router", router_node)
    g.add_node("policy", policy_node)
    g.add_node("metadata", metadata_node)
    g.add_node("sql_gen", sql_gen_node)
    g.add_node("validate", sql_validate_node)
    g.add_node("execute", execute_node)
    g.add_node("answer", answer_node)

    g.set_entry_point("router")

    g.add_conditional_edges(
        "router",
        route_from_router,
        {"refuse": "answer", "clarify": "answer", "policy": "policy"},
    )

    g.add_conditional_edges(
        "policy",
        route_after_policy,
        {"refuse": "answer", "metadata": "metadata", "validate": "validate", "answer": "answer"},
    )

    g.add_conditional_edges(
        "metadata",
        route_after_metadata,
        {"answer": "answer", "sql_gen": "sql_gen"},
    )

    g.add_edge("sql_gen", "validate")

    g.add_conditional_edges(
        "validate",
        route_after_validate,
        {"execute": "execute", "answer": "answer"},
    )

    g.add_edge("execute", "answer")
    g.add_edge("answer", END)

    return g.compile()
