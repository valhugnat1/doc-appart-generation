import json
import operator
from typing import Annotated, Any, Dict, List, Optional, Union, TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

# --- 1. Configuration & Template ---

# --- 2. Helper Functions for JSON Traversal ---


def find_next_missing_field(data: Dict, path: List[str] = []) -> Optional[Dict]:
    """
    Recursively searches for the first field where 'requis' is True
    and 'valeur' is empty/None.
    Returns a dict containing the path, the field schema, and context.
    """
    for key, value in data.items():
        current_path = path + [key]

        # Check if this is a leaf node (has 'valeur' and 'requis')
        if isinstance(value, dict) and "valeur" in value and "requis" in value:
            # Skip if fixed type (already filled)
            if value.get("type") == "fixe":
                continue

            is_empty = value["valeur"] in [None, "", []]
            if value["requis"] and is_empty:
                return {"path": current_path, "schema": value, "key": key}

        # Recurse if it's a nested dictionary (and not a leaf node definition)
        elif isinstance(value, dict):
            result = find_next_missing_field(value, current_path)
            if result:
                return result

        # Handle lists (like 'locataires') - simplified for this example
        # assuming lists contain objects with fields
        elif isinstance(value, list):
            for idx, item in enumerate(value):
                if isinstance(item, dict):
                    result = find_next_missing_field(item, current_path + [str(idx)])
                    if result:
                        return result
    return None


def update_json_value(data: Dict, path: List[str], new_value: Any):
    """Updates the JSON structure at the specific path."""
    ref = data
    for key in path[:-1]:
        # Handle list indices in path if necessary
        if key.isdigit() and isinstance(ref, list):
            ref = ref[int(key)]
        else:
            ref = ref[key]

    last_key = path[-1]
    if last_key.isdigit() and isinstance(ref, list):
        ref[int(last_key)]["valeur"] = new_value
    else:
        ref[last_key]["valeur"] = new_value


# --- 3. State Definition ---


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    contract_data: Dict  # The JSON object
    current_field_info: Optional[Dict]  # Metadata about field currently being asked
    completed: bool


# --- 4. Nodes ---

llm = ChatOpenAI(model="gpt-4o", temperature=0)


def determine_progress(state: AgentState):
    """Analyzes the JSON to find what to do next."""
    data = state.get("contract_data")

    # If no data starts, load the template (logic to load full json would go here)
    if not data:
        # In a real app, load the full blank structure here
        # For the demo, we assume state is initialized with it
        pass

    next_field = find_next_missing_field(data)

    if not next_field:
        return {"completed": True, "current_field_info": None}

    return {"completed": False, "current_field_info": next_field}


def generate_question(state: AgentState):
    """Generates a natural language question for the missing field."""
    field_info = state["current_field_info"]

    # Contextualize the prompt
    path_str = " > ".join(field_info["path"])
    field_type = field_info["schema"].get("type")
    options = field_info["schema"].get("options", [])

    system_prompt = f"""
    You are a helpful French real estate legal assistant filling out a rental contract.
    Your goal is to ask the user for specific information to fill the JSON field: "{path_str}".
    
    Field Type: {field_type}
    Options (if any): {options}
    
    If the field is about "bailleur" (Landlord) or "locataire" (Tenant) or "logement" (Apartment), 
    phrase your question naturally and professionally in French.
    Start with basic questions, then get more specific.
    """

    msg = llm.invoke([SystemMessage(content=system_prompt)])
    return {"messages": [msg]}


def process_answer(state: AgentState):
    """Extracts the value from user input and updates the JSON."""
    messages = state["messages"]
    last_user_msg = messages[-1]
    field_info = state["current_field_info"]

    if not field_info:
        return {}

    # Define a dynamic extraction schema based on the field type
    class Extraction(BaseModel):
        value: Any = Field(description="The extracted value for the field")

    field_type = field_info["schema"].get("type")
    options = field_info["schema"].get("options", [])

    extraction_prompt = f"""
    Extract the value for the field "{field_info['key']}" from the user's text.
    User Input: "{last_user_msg.content}"
    
    Target Type: {field_type}
    allowed Options: {options}
    
    - If type is 'booleen', return boolean true/false.
    - If type is 'nombre', return a number (integer or float).
    - If type is 'date', return format YYYY-MM-DD.
    - If the user provides information that doesn't fit, try to infer logically.
    """

    structured_llm = llm.with_structured_output(Extraction)
    result = structured_llm.invoke(extraction_prompt)

    # Update the main JSON data
    current_data = state["contract_data"]
    update_json_value(current_data, field_info["path"], result.value)

    return {"contract_data": current_data}


def save_contract(state: AgentState):
    """Saves the completed JSON to a file."""
    with open("contrat_finalise.json", "w", encoding="utf-8") as f:
        json.dump(state["contract_data"], f, ensure_ascii=False, indent=2)

    return {
        "messages": [
            AIMessage(
                content="Merci ! Toutes les informations requises ont été collectées. Le contrat a été sauvegardé sous 'contrat_finalise.json'."
            )
        ]
    }


# --- 5. Graph Construction ---

workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("determine_progress", determine_progress)
workflow.add_node("generate_question", generate_question)
workflow.add_node("process_answer", process_answer)
workflow.add_node("save_contract", save_contract)


# Add Edges
def route_after_progress(state: AgentState):
    if state["completed"]:
        return "save_contract"
    return "generate_question"


def route_start(state: AgentState):
    # If this is the very first turn (no history), determine progress immediately
    # If we have history (user just replied), process the answer first
    if len(state["messages"]) > 0 and isinstance(state["messages"][-1], HumanMessage):
        return "process_answer"
    return "determine_progress"


workflow.set_conditional_entry_point(
    route_start,
    {"process_answer": "process_answer", "determine_progress": "determine_progress"},
)

workflow.add_edge("process_answer", "determine_progress")
workflow.add_conditional_edges(
    "determine_progress",
    route_after_progress,
    {"save_contract": "save_contract", "generate_question": "generate_question"},
)
workflow.add_edge("generate_question", END)  # Stop to wait for user input
workflow.add_edge("save_contract", END)

# Compile
app = workflow.compile()
