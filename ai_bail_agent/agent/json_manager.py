import json
import os
import shutil
import threading
from typing import Dict, Any, List, Optional

class JsonManager:
    def __init__(self, template_path: str, sessions_dir: str):
        self.template_path = template_path
        self.sessions_dir = sessions_dir
        self.lock = threading.RLock()
        os.makedirs(sessions_dir, exist_ok=True)

    def _get_session_path(self, session_id: str) -> str:
        return os.path.join(self.sessions_dir, f"{session_id}.json")

    def create_session(self, session_id: str) -> Dict[str, Any]:
        """Creates a new session file from the template if it doesn't exist."""
        with self.lock:
            session_path = self._get_session_path(session_id)
            if not os.path.exists(session_path):
                shutil.copy(self.template_path, session_path)
            return self.load_session(session_id)

    def load_session(self, session_id: str) -> Dict[str, Any]:
        """Loads the session JSON."""
        with self.lock:
            session_path = self._get_session_path(session_id)
            if not os.path.exists(session_path):
                return self.create_session(session_id)
            with open(session_path, 'r', encoding='utf-8') as f:
                return json.load(f)

    def save_session(self, session_id: str, data: Dict[str, Any]):
        """Saves the session JSON."""
        with self.lock:
            session_path = self._get_session_path(session_id)
            with open(session_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

    def update_value(self, session_id: str, path: str, value: Any) -> str:
        """
        Updates a value in the JSON at the specified path.
        Path format: "key1.key2.key3"
        """

        with self.lock:
            data = self.load_session(session_id)
            keys = path.split('.')
            current = data
        
        try:
            for key in keys[:-1]:
                if isinstance(current, list):
                    # Handle list indices if needed, though schema seems mostly dicts
                    # For now assuming dict structure based on provided schema
                    # If list support is needed, we'd need syntax like "locataires.liste[0].nom"
                    # But the schema has lists with objects. 
                    # Let's assume the path handles list indices like "locataires.liste.0.nom"
                    try:
                        idx = int(key)
                        current = current[idx]
                    except ValueError:
                        # If it's a list but key is not int, maybe it's a mistake or special handling
                        return f"Error: Expected index for list, got {key}"
                else:
                    current = current[key]
            
            last_key = keys[-1]
            if isinstance(current, list):
                 try:
                    idx = int(last_key)
                    # This is tricky if we are updating a value inside a list item directly?
                    # But based on schema, values are inside objects "valeur".
                    # So path should end in "valeur" usually.
                    current[idx] = value
                 except ValueError:
                     return f"Error: Expected index for list, got {last_key}"
            else:
                # Special handling for the schema structure where values are in "valeur" key
                # The user might say "set loyer to 500". 
                # The path in JSON is "conditions_financieres.loyer.montant_hors_charges.valeur"
                # The agent needs to be smart about the path or we provide the full path.
                # The prompt says "input: loyer -> 420".
                # This implies the agent or the tool needs to find the right field.
                # For this implementation, I will assume the AGENT provides the FULL path to the 'valeur' field
                # or the parent object. 
                # Let's stick to the instruction: "Set value in the JSON".
                # I'll implement exact path update first.
                
                if last_key not in current:
                     return f"Error: Key {last_key} not found."
                
                # Check if we are updating a leaf node that has "valeur"
                target = current[last_key]
                if isinstance(target, dict) and "valeur" in target:
                    target["valeur"] = value
                else:
                    # Direct update if it's not the specific schema structure or if path points to 'valeur'
                    current[last_key] = value
                    

                    
            self.save_session(session_id, data)
            return "Done"
        except KeyError as e:
            return f"Error: Key not found - {e}"
        except IndexError as e:
            return f"Error: List index out of range - {e}"
        except Exception as e:
            return f"Error: {str(e)}"

    def get_progress(self, session_id: str) -> Dict[str, Dict[str, Any]]:
        """Calculates percentage filled for each top-level category."""
        data = self.load_session(session_id)
        progress = {}
        
        for category, content in data.items():
            total_fields = 0
            filled_fields = 0
            
            # Recursive function to count fields
            def count_fields(obj):
                nonlocal total_fields, filled_fields
                if isinstance(obj, dict):
                    if "valeur" in obj and "requis" in obj:
                        if obj["requis"]:
                            total_fields += 1
                            if obj["valeur"] not in [None, ""]:
                                filled_fields += 1
                    else:
                        for key, value in obj.items():
                            count_fields(value)
                elif isinstance(obj, list):
                    for item in obj:
                        count_fields(item)

            count_fields(content)
            
            if total_fields > 0:
                percentage = int((filled_fields / total_fields) * 100)
                progress[category] = {
                    "percentage": f"{percentage}%",
                    "filled": filled_fields,
                    "total": total_fields
                }
            else:
                progress[category] = {
                    "percentage": "N/A",
                    "filled": 0,
                    "total": 0
                }
                
        return progress

    def get_missing_fields(self, session_id: str, category: str) -> List[str]:
        """Returns a list of missing required fields for a category."""
        data = self.load_session(session_id)
        if category not in data:
            return [f"Category {category} not found"]
            
        missing = []
        
        def find_missing(obj, path=""):
            if isinstance(obj, dict):
                if "valeur" in obj and "requis" in obj:
                    if obj["requis"] and obj["valeur"] in [None, ""]:
                        missing.append(path)
                else:
                    for key, value in obj.items():
                        new_path = f"{path}.{key}" if path else key
                        find_missing(value, new_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    new_path = f"{path}[{i}]"
                    find_missing(item, new_path)

        find_missing(data[category])
        return missing
    def get_all_paths(self) -> List[str]:
        """
        Returns a list of all valid dot-notation paths in the JSON structure.
        Paths point to leaf nodes or nodes containing 'valeur'.
        Examples: 'users.0.email' instead of 'users[0].email'
        """
        # Load from template to ensure we get the full structure
        with open(self.template_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        paths = []
        
        def traverse(obj, current_path=""):
            if isinstance(obj, dict):
                # Check if this is a field with 'valeur' (our target leaf)
                if "valeur" in obj and "requis" in obj:
                    paths.append(current_path)
                else:
                    for key, value in obj.items():
                        new_path = f"{current_path}.{key}" if current_path else key
                        traverse(value, new_path)
            
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    # CHANGE: Use dot notation for indices instead of brackets
                    # If current_path exists, append .i, otherwise just i
                    new_path = f"{current_path}.{i}" if current_path else str(i)
                    traverse(item, new_path)

        traverse(data)
        return paths