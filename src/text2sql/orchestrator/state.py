from __future__ import annotations
from typing import Any, Dict, List, Optional, TypedDict, Literal

Intent = Literal["ASK_METADATA", "GENERATE_SQL", "EXECUTE_SQL", "CLARIFY", "REFUSE"]

class OrchestratorState(TypedDict, total=False):
    # input
    user_message: str
    user_role: str
    provided_sql: Optional[str]

    # routing
    intent: Intent
    entities: Dict[str, Any]
    confidence: float
    needs_clarification: bool
    clarify_question: str

    # guardrails
    allowed: bool
    policy_reason: str

    # metadata
    table_candidates: List[str]
    column_candidates: List[str]

    # sql lifecycle
    sql: str
    sql_ok: bool
    sql_issues: List[str]

    # execution
    result: Any

    # output
    final_answer: str
    errors: List[str]

    # debug
    trace_id: str
