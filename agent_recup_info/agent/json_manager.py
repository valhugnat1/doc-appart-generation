import json
import os
import shutil
import threading
from typing import Dict, Any, List, Optional, Union


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

    def _parse_path(self, path: str) -> List[Union[str, int]]:
        """
        Parse a dot-notation path into a list of keys/indices.
        Supports both:
        - "locataires.liste.0.nom_prenom" (dot notation for indices)
        - "locataires.liste[0].nom_prenom" (bracket notation for indices)
        """
        # First, convert bracket notation to dot notation for uniformity
        # e.g., "liste[0].nom" -> "liste.0.nom"
        import re
        normalized = re.sub(r'\[(\d+)\]', r'.\1', path)
        
        parts = normalized.split('.')
        result = []
        for part in parts:
            if part.isdigit():
                result.append(int(part))
            else:
                result.append(part)
        return result

    def _navigate_to_parent(self, data: Dict, keys: List[Union[str, int]]) -> tuple:
        """
        Navigate to the parent of the target key.
        Returns (parent_object, final_key) or raises an error.
        """
        current = data
        for key in keys[:-1]:
            if isinstance(current, list):
                if not isinstance(key, int):
                    raise ValueError(f"Expected integer index for list, got '{key}'")
                if key < 0 or key >= len(current):
                    raise IndexError(f"List index {key} out of range (list has {len(current)} items)")
                current = current[key]
            elif isinstance(current, dict):
                if key not in current:
                    raise KeyError(f"Key '{key}' not found in object")
                current = current[key]
            else:
                raise TypeError(f"Cannot navigate through {type(current).__name__}")
        
        return current, keys[-1]

    def update_value(self, session_id: str, path: str, value: Any) -> str:
        """
        Updates a value in the JSON at the specified path.
        Path format: "key1.key2.0.key3" or "key1.key2[0].key3"
        
        Automatically handles the schema structure where values are in "valeur" fields.
        """
        with self.lock:
            data = self.load_session(session_id)
            
            try:
                keys = self._parse_path(path)
                parent, final_key = self._navigate_to_parent(data, keys)
                
                # Handle the final key
                if isinstance(parent, list):
                    if not isinstance(final_key, int):
                        return f"Error: Expected integer index for list, got '{final_key}'"
                    if final_key < 0 or final_key >= len(parent):
                        return f"Error: List index {final_key} out of range"
                    
                    target = parent[final_key]
                    if isinstance(target, dict) and "valeur" in target:
                        target["valeur"] = value
                    else:
                        parent[final_key] = value
                else:
                    if final_key not in parent:
                        return f"Error: Key '{final_key}' not found"
                    
                    target = parent[final_key]
                    if isinstance(target, dict) and "valeur" in target:
                        target["valeur"] = value
                    else:
                        parent[final_key] = value
                
                self.save_session(session_id, data)
                return "Done"
                
            except (KeyError, IndexError, ValueError, TypeError) as e:
                return f"Error: {str(e)}"
            except Exception as e:
                return f"Error: Unexpected error - {str(e)}"

    def add_list_item(self, session_id: str, list_path: str, item_template: Optional[Dict] = None) -> str:
        """
        Adds a new item to a list at the specified path.
        If item_template is None, copies the structure of the first item in the list.
        
        Returns the index of the newly added item.
        """
        with self.lock:
            data = self.load_session(session_id)
            
            try:
                keys = self._parse_path(list_path)
                
                # Navigate to the list
                current = data
                for key in keys:
                    if isinstance(current, list):
                        if not isinstance(key, int):
                            return f"Error: Expected integer index for list, got '{key}'"
                        current = current[key]
                    elif isinstance(current, dict):
                        if key not in current:
                            return f"Error: Key '{key}' not found"
                        current = current[key]
                    else:
                        return f"Error: Cannot navigate through {type(current).__name__}"
                
                if not isinstance(current, list):
                    return f"Error: Path '{list_path}' does not point to a list"
                
                # Create new item
                if item_template is not None:
                    new_item = item_template
                elif len(current) > 0:
                    # Deep copy the first item and reset all values
                    new_item = self._create_empty_copy(current[0])
                else:
                    return "Error: Cannot add item - list is empty and no template provided"
                
                current.append(new_item)
                new_index = len(current) - 1
                
                self.save_session(session_id, data)
                return f"Done. New item added at index {new_index}"
                
            except Exception as e:
                return f"Error: {str(e)}"

    def remove_list_item(self, session_id: str, list_path: str, index: int) -> str:
        """
        Removes an item from a list at the specified path and index.
        """
        with self.lock:
            data = self.load_session(session_id)
            
            try:
                keys = self._parse_path(list_path)
                
                # Navigate to the list
                current = data
                for key in keys:
                    if isinstance(current, list):
                        if not isinstance(key, int):
                            return f"Error: Expected integer index for list, got '{key}'"
                        current = current[key]
                    elif isinstance(current, dict):
                        if key not in current:
                            return f"Error: Key '{key}' not found"
                        current = current[key]
                    else:
                        return f"Error: Cannot navigate through {type(current).__name__}"
                
                if not isinstance(current, list):
                    return f"Error: Path '{list_path}' does not point to a list"
                
                if index < 0 or index >= len(current):
                    return f"Error: Index {index} out of range (list has {len(current)} items)"
                
                # Don't allow removing the last item (keep at least one for template)
                if len(current) <= 1:
                    return "Error: Cannot remove the last item from the list"
                
                current.pop(index)
                self.save_session(session_id, data)
                return f"Done. Item at index {index} removed"
                
            except Exception as e:
                return f"Error: {str(e)}"

    def get_list_length(self, session_id: str, list_path: str) -> Union[int, str]:
        """
        Returns the number of items in a list at the specified path.
        """
        data = self.load_session(session_id)
        
        try:
            keys = self._parse_path(list_path)
            
            current = data
            for key in keys:
                if isinstance(current, list):
                    if not isinstance(key, int):
                        return f"Error: Expected integer index for list, got '{key}'"
                    current = current[key]
                elif isinstance(current, dict):
                    if key not in current:
                        return f"Error: Key '{key}' not found"
                    current = current[key]
                else:
                    return f"Error: Cannot navigate through {type(current).__name__}"
            
            if not isinstance(current, list):
                return f"Error: Path '{list_path}' does not point to a list"
            
            return len(current)
            
        except Exception as e:
            return f"Error: {str(e)}"

    def _create_empty_copy(self, obj: Any) -> Any:
        """
        Creates a deep copy of an object with all 'valeur' fields reset to empty/null.
        """
        if isinstance(obj, dict):
            if "valeur" in obj and "requis" in obj:
                # This is a field object - reset the value
                copy = obj.copy()
                if obj.get("type") == "booleen":
                    copy["valeur"] = None
                elif obj.get("type") == "nombre":
                    copy["valeur"] = None
                else:
                    copy["valeur"] = ""
                return copy
            else:
                return {k: self._create_empty_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._create_empty_copy(item) for item in obj]
        else:
            return obj

    def get_progress(self, session_id: str) -> Dict[str, Dict[str, Any]]:
        """Calculates percentage filled for each top-level category."""
        data = self.load_session(session_id)
        progress = {}
        
        for category, content in data.items():
            total_fields = 0
            filled_fields = 0
            
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
            return [f"Category '{category}' not found"]
            
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
                    new_path = f"{path}.{i}"
                    find_missing(item, new_path)

        find_missing(data[category])
        return missing

    def get_all_paths(self, include_list_indices: bool = True) -> List[str]:
        """
        Returns a list of all valid dot-notation paths in the JSON structure.
        Paths point to leaf nodes (fields with 'valeur').
        
        If include_list_indices is True, includes paths like 'locataires.liste.0.nom_prenom'.
        Also includes list paths like 'locataires.liste' for add/remove operations.
        """
        with open(self.template_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        paths = []
        list_paths = []
        
        def traverse(obj, current_path=""):
            if isinstance(obj, dict):
                if "valeur" in obj and "requis" in obj:
                    paths.append(current_path)
                else:
                    for key, value in obj.items():
                        new_path = f"{current_path}.{key}" if current_path else key
                        traverse(value, new_path)
            
            elif isinstance(obj, list):
                list_paths.append(current_path)
                if include_list_indices:
                    for i, item in enumerate(obj):
                        new_path = f"{current_path}.{i}"
                        traverse(item, new_path)

        traverse(data)
        return {"field_paths": paths, "list_paths": list_paths}

    def get_list_items_info(self, session_id: str, list_path: str) -> str:
        """
        Returns information about all items in a list, including their current values.
        Useful for the agent to understand what's already filled.
        """
        data = self.load_session(session_id)
        
        try:
            keys = self._parse_path(list_path)
            
            current = data
            for key in keys:
                if isinstance(current, list):
                    current = current[int(key)]
                elif isinstance(current, dict):
                    current = current[key]
            
            if not isinstance(current, list):
                return f"Error: Path '{list_path}' does not point to a list"
            
            result = [f"List '{list_path}' has {len(current)} item(s):"]
            
            for i, item in enumerate(current):
                result.append(f"\n  Item {i}:")
                self._format_item(item, "    ", result)
            
            return "\n".join(result)
            
        except Exception as e:
            return f"Error: {str(e)}"

    def _format_item(self, obj: Any, indent: str, result: List[str]):
        """Helper to format an item for display."""
        if isinstance(obj, dict):
            if "valeur" in obj and "requis" in obj:
                status = "✓" if obj["valeur"] not in [None, ""] else "✗"
                val_display = obj["valeur"] if obj["valeur"] not in [None, ""] else "(empty)"
                result.append(f"{indent}{status} valeur: {val_display}")
            else:
                for key, value in obj.items():
                    if isinstance(value, dict):
                        if "valeur" in value:
                            status = "✓" if value["valeur"] not in [None, ""] else "✗"
                            val_display = value["valeur"] if value["valeur"] not in [None, ""] else "(empty)"
                            req = " (required)" if value.get("requis") else ""
                            result.append(f"{indent}{status} {key}: {val_display}{req}")
                        else:
                            result.append(f"{indent}{key}:")
                            self._format_item(value, indent + "  ", result)