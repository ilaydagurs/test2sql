from typing import Any, Dict

def text2sql(question: str, role: str, debug: bool = False) -> Dict[str, Any]:
    return {
        "sql": "SELECT 1 as demo",
        "answer": f"demo cevap (role={role}) | soru: {question}",
        "trace": {"debug": debug, "note": "graph_client mock çalıştı"}
    }
