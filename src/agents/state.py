from enum import Enum
from typing import Optional, Any, Annotated
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class IntentEnum(str, Enum):
    GENERAL = "GENERAL"
    DATA_QUERY = "DATA_QUERY"
    RETENTION_DOC = "RETENTION_DOC"

class AgentState(TypedDict):
    """
    State schema for the PeopleRisk AI multi-agent graph.
    """
    messages: Annotated[list[AnyMessage], add_messages]
    current_intent: Optional[IntentEnum]
    extracted_data: Optional[Any]
