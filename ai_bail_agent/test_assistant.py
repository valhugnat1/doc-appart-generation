"""
Test suite for the French Lease Assistant
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.json_manager import JSONManager
from utils.memory_manager import MemoryManager
from agent.tools import (
    initialize_managers,
    get_global_progress,
    get_section_details,
    set_field_value,
    get_missing_required_fields,
    validate_document,
    extract_information_from_text,
)


class TestJSONManager:
    """Test JSON Manager functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.template_path = Path(self.temp_dir) / "template.json"
        self.sessions_dir = Path(self.temp_dir) / "sessions"

        # Create a minimal template
        template_data = {
            "test_section": {
                "field1": {"valeur": "", "requis": True, "type": "texte"},
                "field2": {"valeur": "", "requis": False, "type": "nombre"},
            }
        }

        with open(self.template_path, "w") as f:
            json.dump(template_data, f)

        self.json_manager = JSONManager(
            template_path=str(self.template_path), sessions_dir=str(self.sessions_dir)
        )

    def test_create_session(self):
        """Test session creation"""
        session_id = "test-session-123"
        file_path = self.json_manager.create_session_json(session_id)

        assert Path(file_path).exists()

        data = self.json_manager.load_session_json(session_id)
        assert "_metadata" in data
        assert data["_metadata"]["session_id"] == session_id

    def test_set_and_get_field_value(self):
        """Test setting and getting field values"""
        session_id = "test-session-456"
        self.json_manager.create_session_json(session_id)

        # Set a value
        success = self.json_manager.set_field_value(
            session_id, "test_section.field1.valeur", "Test Value"
        )
        assert success == True

        # Get the value
        value = self.json_manager.get_field_value(
            session_id, "test_section.field1.valeur"
        )
        assert value == "Test Value"

    def test_completion_status(self):
        """Test completion status calculation"""
        session_id = "test-session-789"
        self.json_manager.create_session_json(session_id)

        # Initially empty
        status = self.json_manager.get_completion_status(session_id)
        assert status["overall_percentage"] == 0.0

        # Fill one field
        self.json_manager.set_field_value(
            session_id, "test_section.field1.valeur", "Filled"
        )

        status = self.json_manager.get_completion_status(session_id)
        assert status["overall_percentage"] == 50.0  # 1 out of 2 fields

    def test_missing_required_fields(self):
        """Test getting missing required fields"""
        session_id = "test-session-999"
        self.json_manager.create_session_json(session_id)

        missing = self.json_manager.get_missing_required_fields(session_id)
        assert len(missing) == 1  # Only field1 is required
        assert missing[0][0] == "test_section.field1.valeur"

    def test_validate_document(self):
        """Test document validation"""
        session_id = "test-session-000"
        self.json_manager.create_session_json(session_id)

        # Initially invalid
        validation = self.json_manager.validate_document(session_id)
        assert validation["is_complete"] == False

        # Fill required field
        self.json_manager.set_field_value(
            session_id, "test_section.field1.valeur", "Required Value"
        )

        validation = self.json_manager.validate_document(session_id)
        assert validation["is_complete"] == True


class TestMemoryManager:
    """Test Memory Manager functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.memory_dir = Path(self.temp_dir) / "memory"
        self.memory_manager = MemoryManager(memory_dir=str(self.memory_dir))

    def test_create_session(self):
        """Test creating a new session"""
        session_id = self.memory_manager.create_session()

        assert session_id is not None
        assert len(session_id) == 36  # UUID format

        # Check file was created
        memory_file = self.memory_dir / f"{session_id}.json"
        assert memory_file.exists()

    def test_load_session(self):
        """Test loading a session"""
        session_id = self.memory_manager.create_session()
        memory = self.memory_manager.load_session(session_id)

        assert memory["session_id"] == session_id
        assert "conversation_history" in memory
        assert "collected_information" in memory

    def test_add_conversation_turn(self):
        """Test adding conversation turns"""
        session_id = self.memory_manager.create_session()

        self.memory_manager.add_conversation_turn(
            session_id, "User message", "Assistant response", {"field1": "value1"}
        )

        memory = self.memory_manager.load_session(session_id)
        assert len(memory["conversation_history"]) == 1
        assert memory["conversation_history"][0]["user"] == "User message"
        assert memory["collected_information"]["field1"] == "value1"

    def test_get_conversation_summary(self):
        """Test conversation summary generation"""
        session_id = self.memory_manager.create_session()

        # Empty conversation
        summary = self.memory_manager.get_conversation_summary(session_id)
        assert summary == "Nouvelle conversation"

        # Add some turns
        self.memory_manager.add_conversation_turn(
            session_id, "Test user message", "Test assistant response", {"loyer": 1500}
        )

        summary = self.memory_manager.get_conversation_summary(session_id)
        assert "loyer=1500" in summary


class TestTools:
    """Test agent tools"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()

        # Create managers
        template_path = Path(self.temp_dir) / "template.json"

        # Create a more complete template for testing
        template_data = {
            "designation_parties": {
                "bailleur": {
                    "nom_prenom_ou_denomination": {
                        "valeur": "",
                        "requis": True,
                        "type": "texte",
                    }
                }
            },
            "conditions_financieres": {
                "loyer": {
                    "montant_hors_charges": {
                        "valeur": None,
                        "requis": True,
                        "type": "nombre",
                    }
                }
            },
        }

        with open(template_path, "w") as f:
            json.dump(template_data, f)

        self.json_manager = JSONManager(
            template_path=str(template_path),
            sessions_dir=str(Path(self.temp_dir) / "sessions"),
        )
        self.memory_manager = MemoryManager(
            memory_dir=str(Path(self.temp_dir) / "memory")
        )

        # Initialize tools with managers
        initialize_managers(self.json_manager, self.memory_manager)

        # Create a test session
        self.session_id = "test-tools-session"
        self.json_manager.create_session_json(self.session_id)

    def test_get_global_progress(self):
        """Test global progress tool"""
        result = get_global_progress.invoke({"session_id": self.session_id})

        assert "overall_completion" in result
        assert "sections" in result
        assert result["filled_fields"] == 0

    def test_set_field_value_tool(self):
        """Test set field value tool"""
        result = set_field_value.invoke(
            {
                "session_id": self.session_id,
                "field_path": "designation_parties.bailleur.nom_prenom_ou_denomination.valeur",
                "value": "Jean Dupont",
            }
        )

        assert result["status"] == "success"
        assert result["value"] == "Jean Dupont"

    def test_get_missing_required_fields(self):
        """Test getting missing required fields"""
        result = get_missing_required_fields.invoke(
            {"session_id": self.session_id, "section_filter": None}
        )

        assert result["total_missing"] == 2  # Both required fields are empty
        assert "by_section" in result

    def test_validate_document(self):
        """Test document validation tool"""
        result = validate_document.invoke({"session_id": self.session_id})

        assert result["is_complete"] == False
        assert result["can_generate"] == False
        assert "missing_required_count" in result

    def test_extract_information_from_text(self):
        """Test information extraction from text"""
        text = """
        Le loyer sera de 1500€ par mois.
        L'appartement fait 65 m² avec 3 pièces.
        Mon email est jean.dupont@example.com
        Le bail commence le 01/01/2024.
        """

        result = extract_information_from_text.invoke(
            {"session_id": self.session_id, "text": text}
        )

        assert "extracted_information" in result
        extracted = result["extracted_information"]

        assert "amounts" in extracted
        assert "1500" in extracted["amounts"][0]
        assert "surface" in extracted
        assert "65" in extracted["surface"]
        assert "emails" in extracted
        assert "jean.dupont@example.com" in extracted["emails"]


class TestIntegration:
    """Integration tests for the complete system"""

    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"),
        reason="No API key available for integration test",
    )
    def test_full_conversation_flow(self):
        """Test a complete conversation flow"""
        from main import FrenchLeaseAssistant

        # Initialize assistant
        assistant = FrenchLeaseAssistant()

        # Create session
        session_id = assistant.new_session()
        assert session_id is not None

        # Have a conversation
        response = assistant.chat(
            session_id, "Je veux louer un appartement. Le loyer est de 1200€"
        )
        assert response is not None
        assert len(response) > 0

        # Check status
        status = assistant.get_session_status(session_id)
        assert "overall_completion" in status
        assert status["overall_completion"] > 0  # Some progress made

        # Try to export (should fail as incomplete)
        export_result = assistant.export_lease(session_id)
        assert export_result["status"] == "incomplete"


def run_tests():
    """Run all tests"""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    run_tests()
