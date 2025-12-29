from typing import TypedDict, List, Optional, Annotated
import operator

class AgentState(TypedDict):
    user_id: str
    user_role: str
    question: str

    intent: str
    schema_info: str
    selected_model: str

    sql_query: str
    sql_error: Optional[str]

    query_result: Optional[list]
    chart_spec: Optional[dict]
    explanation: Optional[str]

    final_response: dict
    logs: Annotated[List[str], operator.add]