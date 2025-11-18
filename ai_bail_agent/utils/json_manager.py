"""
JSON Manager for handling lease document operations
"""

import json
import os
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import shutil
from datetime import datetime


class JSONManager:
    """Manages JSON operations for lease documents"""

    def __init__(
        self,
        template_path: str = "data/template_data.json",
        sessions_dir: str = "data/sessions",
    ):
        self.template_path = Path(template_path)
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self._template_cache = None

    @property
    def template(self) -> Dict[str, Any]:
        """Load and cache the template"""
        if self._template_cache is None:
            with open(self.template_path, "r", encoding="utf-8") as f:
                self._template_cache = json.load(f)
        return self._template_cache

    def reload_template(self):
        """Force reload of the template (useful when template changes)"""
        self._template_cache = None
        return self.template

    def create_session_json(self, session_id: str) -> str:
        """Create a new JSON file for a session from template"""
        session_file = self.sessions_dir / f"{session_id}.json"

        # Copy template to session file
        with open(self.template_path, "r", encoding="utf-8") as f:
            template_data = json.load(f)

        # Add session metadata
        template_data["_metadata"] = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "completion_percentage": 0.0,
        }

        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(template_data, f, ensure_ascii=False, indent=2)

        return str(session_file)

    def load_session_json(self, session_id: str) -> Dict[str, Any]:
        """Load a session's JSON file"""
        session_file = self.sessions_dir / f"{session_id}.json"
        if not session_file.exists():
            raise FileNotFoundError(f"Session file not found: {session_id}")

        with open(session_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_session_json(self, session_id: str, data: Dict[str, Any]):
        """Save data to a session's JSON file"""
        session_file = self.sessions_dir / f"{session_id}.json"

        # Update metadata
        if "_metadata" in data:
            data["_metadata"]["last_modified"] = datetime.now().isoformat()

        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def set_field_value(self, session_id: str, field_path: str, value: Any) -> bool:
        """Set a specific field value in the JSON"""
        data = self.load_session_json(session_id)

        # Navigate the path and set the value
        keys = field_path.split(".")
        current = data

        try:
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]

            # Handle the last key specially to preserve field structure
            last_key = keys[-1]
            if last_key in current and isinstance(current[last_key], dict):
                if "valeur" in current[last_key]:
                    current[last_key]["valeur"] = value
                else:
                    current[last_key] = value
            else:
                current[last_key] = value

            self.save_session_json(session_id, data)
            return True
        except Exception as e:
            print(f"Error setting field {field_path}: {e}")
            return False

    def get_field_value(self, session_id: str, field_path: str) -> Any:
        """Get a specific field value from the JSON"""
        data = self.load_session_json(session_id)

        keys = field_path.split(".")
        current = data

        try:
            for key in keys:
                current = current[key]

            # If it's a field object with 'valeur', return the value
            if isinstance(current, dict) and "valeur" in current:
                return current["valeur"]
            return current
        except (KeyError, TypeError):
            return None

    def get_all_fields_flat(
        self, data: Dict[str, Any], prefix: str = ""
    ) -> Dict[str, Any]:
        """Flatten the JSON structure to get all fields with their paths"""
        fields = {}

        for key, value in data.items():
            if key.startswith("_"):  # Skip metadata
                continue

            current_path = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict):
                if "valeur" in value and "requis" in value:
                    # This is a field definition
                    fields[current_path] = {
                        "value": value.get("valeur"),
                        "required": value.get("requis", False),
                        "type": value.get("type", "texte"),
                    }
                else:
                    # Nested structure, recurse
                    fields.update(self.get_all_fields_flat(value, current_path))
            elif isinstance(value, list) and key == "liste":
                # Handle list structures
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        fields.update(self.get_all_fields_flat(item, f"{prefix}[{i}]"))

        return fields

    def get_completion_status(self, session_id: str) -> Dict[str, Any]:
        """Calculate completion status for the document"""
        data = self.load_session_json(session_id)
        all_fields = self.get_all_fields_flat(data)

        # Calculate by section
        sections = {}
        for field_path, field_info in all_fields.items():
            section = field_path.split(".")[0]
            if section not in sections:
                sections[section] = {"total": 0, "filled": 0, "required_missing": []}

            sections[section]["total"] += 1

            if field_info["value"] not in [None, "", []]:
                sections[section]["filled"] += 1
            elif field_info["required"]:
                sections[section]["required_missing"].append(field_path)

        # Calculate percentages
        for section in sections:
            total = sections[section]["total"]
            filled = sections[section]["filled"]
            sections[section]["percentage"] = (filled / total * 100) if total > 0 else 0

        # Overall completion
        total_fields = sum(s["total"] for s in sections.values())
        filled_fields = sum(s["filled"] for s in sections.values())
        overall_percentage = (
            (filled_fields / total_fields * 100) if total_fields > 0 else 0
        )

        return {
            "overall_percentage": overall_percentage,
            "sections": sections,
            "total_fields": total_fields,
            "filled_fields": filled_fields,
        }

    def get_missing_required_fields(self, session_id: str) -> List[Tuple[str, str]]:
        """Get all missing required fields with their types"""
        data = self.load_session_json(session_id)
        all_fields = self.get_all_fields_flat(data)

        missing = []
        for field_path, field_info in all_fields.items():
            if field_info["required"] and field_info["value"] in [None, "", []]:
                missing.append((field_path, field_info["type"]))

        return missing

    def validate_document(self, session_id: str) -> Dict[str, Any]:
        """Validate if the document is ready"""
        missing_required = self.get_missing_required_fields(session_id)
        completion_status = self.get_completion_status(session_id)

        return {
            "is_complete": len(missing_required) == 0,
            "missing_required_count": len(missing_required),
            "missing_required_fields": missing_required,
            "overall_completion": completion_status["overall_percentage"],
            "can_generate_document": len(missing_required) == 0,
        }
