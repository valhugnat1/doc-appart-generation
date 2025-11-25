from langchain_core.tools import tool, StructuredTool
from typing import List, Dict, Any, Optional
from agent.json_manager import JsonManager
import os

# Initialize JsonManager
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATE_PATH = os.path.join(BASE_DIR, "data", "template_data.json")
SESSIONS_DIR = os.path.join(BASE_DIR, "data", "sessions")

json_manager = JsonManager(TEMPLATE_PATH, SESSIONS_DIR)


@tool
def get_global_feedback(session_id: str) -> str:
    """
    Get a global feedback on which big parts are filled, focusing on mandatory elements.
    Returns a string with percentages and counts of mandatory fields for each category.
    
    Use this tool at the start of a conversation or when you need an overview.
    """
    progress = json_manager.get_progress(session_id)
    lines = ["=== Progress Overview ==="]
    for category, stats in progress.items():
        if isinstance(stats, dict):
            lines.append(f"{category}: {stats['percentage']} ({stats['filled']}/{stats['total']} mandatory fields filled)")
        else:
            lines.append(f"{category}: {stats}")
    
    # Also show list counts
    lines.append("\n=== List Items ===")
    list_info = [
        ("designation_parties.locataires.liste", "Locataires"),
        ("designation_parties.garants.liste", "Garants"),
    ]
    
    for list_path, label in list_info:
        count = json_manager.get_list_length(session_id, list_path)
        if isinstance(count, int):
            lines.append(f"{label}: {count} item(s)")
        else:
            lines.append(f"{label}: Error getting count")
            
    return "\n".join(lines)


@tool
def get_part_detail(session_id: str, categories: List[str]) -> str:
    """
    Get details of multiple big parts knowledge.
    Returns a list of missing required fields for each specified category.
    
    Input: 
        - session_id: The session identifier
        - categories: List of category names (e.g., ["duree_contrat", "designation_parties"])
    
    For list items (locataires, garants), paths will include the index like:
    "locataires.liste.0.nom_prenom" for the first locataire's name.
    """
    results = []
    for category in categories:
        missing = json_manager.get_missing_fields(session_id, category)
        if missing:
            results.append(f"Missing fields in '{category}':")
            for field in missing:
                results.append(f"  - {category}.{field}")
        else:
            results.append(f"'{category}': All required fields are filled!")
    return "\n".join(results)


@tool
def get_list_info(session_id: str, list_path: str) -> str:
    """
    Get information about items in a list (locataires, garants, etc.).
    Shows the current values and status of each item in the list.
    
    Input:
        - session_id: The session identifier
        - list_path: Path to the list, e.g., "designation_parties.locataires.liste" or "designation_parties.garants.liste"
    
    Common list paths:
        - designation_parties.locataires.liste (tenants)
        - designation_parties.garants.liste (guarantors)
    """
    return json_manager.get_list_items_info(session_id, list_path)


@tool
def add_list_item(session_id: str, list_path: str) -> str:
    """
    Add a new empty item to a list (for adding additional locataires, garants, etc.).
    The new item will be created with the same structure as existing items but with empty values.
    
    Input:
        - session_id: The session identifier
        - list_path: Path to the list, e.g., "designation_parties.locataires.liste"
    
    Returns the index of the newly added item. Use this index in subsequent set_value calls.
    
    Example workflow:
        1. add_list_item(session_id, "designation_parties.locataires.liste") -> "Done. New item added at index 1"
        2. set_value(session_id, [{path: "designation_parties.locataires.liste.1.nom_prenom", value: "Jean Dupont"}])
    """
    return json_manager.add_list_item(session_id, list_path)


@tool
def remove_list_item(session_id: str, list_path: str, index: int) -> str:
    """
    Remove an item from a list at the specified index.
    Note: Cannot remove the last remaining item in a list.
    
    Input:
        - session_id: The session identifier
        - list_path: Path to the list, e.g., "designation_parties.locataires.liste"
        - index: The index of the item to remove (0-based)
    
    Warning: Removing an item will shift the indices of all subsequent items!
    """
    return json_manager.remove_list_item(session_id, list_path, index)


def set_value_impl(session_id: str, updates: List[Dict[str, Any]]) -> str:
    """
    Set multiple values in the JSON.
    """
    results = []
    for update in updates:
        path = update.get("path")
        value = update.get("value")
        
        if not path or value is None:
            results.append(f"Error: Invalid update format for {update}")
            continue

        # Attempt to parse value if it looks like a number or boolean
        parsed_value = value
        if isinstance(value, str):
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
                    pass  # Keep as string
        
        result = json_manager.update_value(session_id, path, parsed_value)
        results.append(f"Update '{path}': {result}")

    return "\n".join(results)


# Generate dynamic description with paths
all_paths_info = json_manager.get_all_paths()
field_paths = all_paths_info.get("field_paths", [])
list_paths = all_paths_info.get("list_paths", [])

formatted_field_paths = "\n".join([f"  - {p}" for p in field_paths])
formatted_list_paths = "\n".join([f"  - {p}" for p in list_paths])

set_value_description = f"""
Set multiple values in the JSON at once.

Input:
    - session_id: The session identifier
    - updates: List of dictionaries, each with "path" and "value" keys
    
Example:
    set_value(session_id, [
        {{"path": "designation_parties.locataires.liste.0.nom_prenom", "value": "Marie Dupont"}},
        {{"path": "designation_parties.locataires.liste.0.email", "value": "marie@email.com"}},
        {{"path": "conditions_financieres.loyer.montant_hors_charges", "value": "800"}}
    ])

**Path Format:**
- Use dot notation: "category.subcategory.field"
- For list items, use index: "designation_parties.locataires.liste.0.nom_prenom" (first tenant)
- The tool automatically updates the "valeur" field in the schema structure

**Lists in the schema (use add_list_item to add more):**
{formatted_list_paths}

**Available Field Paths:**
{formatted_field_paths}
"""

set_value = StructuredTool.from_function(
    func=set_value_impl,
    name="set_value",
    description=set_value_description
)


# Export all tools
__all__ = [
    'get_global_feedback',
    'get_part_detail', 
    'get_list_info',
    'add_list_item',
    'remove_list_item',
    'set_value'
]