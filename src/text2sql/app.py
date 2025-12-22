from __future__ import annotations
import uuid
from typing import Optional

from text2sql.orchestrator.graph import build_app
from text2sql.orchestrator.state import OrchestratorState


def run(user_message: str, user_role: str, sql: Optional[str] = None) -> OrchestratorState:
    app = build_app()
    state: OrchestratorState = {
        "user_message": user_message,
        "user_role": user_role,
        "provided_sql": sql,
        "errors": [],
        "trace_id": str(uuid.uuid4()),
    }
    return app.invoke(state)
