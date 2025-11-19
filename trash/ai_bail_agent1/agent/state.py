"""
State management for the French Lease Agent
"""

import operator
from typing import TypedDict, Annotated, List, Dict, Any, Optional, Literal
from langchain_core.messages import AnyMessage


class ConversationMemory(TypedDict):
    """Memory structure for conversation context"""

    session_id: str
    current_topic: Optional[str]
    last_asked_fields: List[str]
    conversation_history: List[Dict[str, Any]]
    collected_information: Dict[str, Any]


class AgentState(TypedDict):
    """Main state for the agent"""

    messages: Annotated[List[AnyMessage], operator.add]
    session_id: str
    memory: ConversationMemory
    current_json_state: Dict[str, Any]
    missing_required_fields: List[str]
    completion_percentage: float
    last_tool_outputs: Optional[Dict[str, Any]]
    retries: int
    next_action: Optional[Literal["ask_question", "validate", "complete"]]
