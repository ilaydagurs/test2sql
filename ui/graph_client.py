from core.graph import build_graph
_graph = None

def run_question(user_id, user_role, question):
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph.invoke({
        "user_id": user_id,
        "user_role": user_role,
        "question": question,
        "logs": []
    })