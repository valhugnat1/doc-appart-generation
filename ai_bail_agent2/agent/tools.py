from langchain_core.tools import tool
from agent.json_manager import JsonManager
import os

# Initialize JsonManager (assuming running from root)
# We need a way to pass the session_id to the tools. 
# In LangGraph, we can pass it via the state or configuration.
# But standard tools usually take arguments.
# We will assume the agent passes 'session_id' as an argument to the tools.

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(BASE_DIR, "data", "template_data.json")
SESSIONS_DIR = os.path.join(BASE_DIR, "data", "sessions")

json_manager = JsonManager(TEMPLATE_PATH, SESSIONS_DIR)

@tool
def get_global_feedback(session_id: str) -> str:
    """
    Get a global feedback on which big parts are filled.
    Returns a string with percentages for each category.
    """
    progress = json_manager.get_progress(session_id)
    return str(progress)

@tool
def get_part_detail(session_id: str, category: str) -> str:
    """
    Get details of a big part knowledge.
    Returns a list of missing required fields for the specified category.
    Input: session_id, category (e.g., "duree_contrat")
    """
    missing = json_manager.get_missing_fields(session_id, category)
    return f"Missing fields in {category}: {missing}"

@tool
def set_value(session_id: str, path: str, value: str) -> str:
    """
    Set a value in the JSON.
    Input: session_id, path (dot notation, e.g., "conditions_financieres.loyer.montant_hors_charges"), value.
    The tool automatically targets the 'valeur' field if the path points to a field object.
    """
    # Attempt to parse value if it looks like a number or boolean
    parsed_value = value
    if value.lower() == "true":
        parsed_value = True
    elif value.lower() == "false":
        parsed_value = False
    else:
        try:
            if "." in value:
                parsed_value = float(value)
            else:
                parsed_value = int(value)
        except ValueError:
            pass # Keep as string

    return json_manager.update_value(session_id, path, parsed_value)
