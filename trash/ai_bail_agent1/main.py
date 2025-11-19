"""
Main application for the French Lease Assistant
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import MemorySaver

from agent.agent_builder import create_lease_agent, get_system_message
from utils.json_manager import JSONManager
from utils.memory_manager import MemoryManager


class FrenchLeaseAssistant:
    """Main class for the French Lease Assistant application"""

    def __init__(self, model_name: str = None, api_key: str = None):
        """
        Initialize the French Lease Assistant

        Args:
            model_name: LLM model to use
            api_key: API key for the model
        """
        # Initialize managers
        self.json_manager = JSONManager()
        self.memory_manager = MemoryManager()

        # Initialize LLM
        self.llm = self._initialize_llm(model_name, api_key)

        # Create agent
        self.agent = create_lease_agent(
            self.llm, self.json_manager, self.memory_manager
        )

        # Get system message
        self.system_message = get_system_message()

        # Active sessions
        self.active_sessions = {}

    def _initialize_llm(self, model_name: Optional[str], api_key: Optional[str]):
        """Initialize the language model"""
        # You can customize this based on your needs
        # For example, using OpenAI, Anthropic, or local models

        if model_name and "gpt" in model_name.lower():
            # OpenAI
            return init_chat_model(
                model=model_name or "gpt-4",
                model_provider="openai",
                api_key=api_key or os.getenv("OPENAI_API_KEY"),
            )
        elif model_name and "claude" in model_name.lower():
            # Anthropic
            return init_chat_model(
                model=model_name or "claude-4-5-sonnet-lastest",
                model_provider="anthropic",
                api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
            )
        else:
            # Default to a local or open model
            # You can adjust this based on your setup
            try:
                return init_chat_model(
                    model=model_name or "gpt-3.5-turbo",
                    model_provider="openai",
                    api_key=api_key
                    or os.getenv("OPENAI_API_KEY", "dummy-key-for-testing"),
                )
            except:
                # Fallback for testing without API key
                print(
                    "Warning: No valid LLM configuration found. Using mock LLM for testing."
                )
                from langchain_core.language_models import FakeListLLM

                return FakeListLLM(responses=["Test response"])

    def new_session(self) -> str:
        """
        Start a new conversation session

        Returns:
            session_id: Unique identifier for the session
        """
        # Create new session in memory manager
        session_id = self.memory_manager.create_session()

        # Create new JSON file for this session
        self.json_manager.create_session_json(session_id)

        # Store session info
        self.active_sessions[session_id] = {
            "created_at": datetime.now().isoformat(),
            "message_count": 0,
        }

        print(f"✨ New session created: {session_id}")
        return session_id

    def chat(self, session_id: str, user_message: str) -> str:
        """
        Process a user message in a conversation

        Args:
            session_id: The session identifier
            user_message: The user's message

        Returns:
            The assistant's response
        """
        if session_id not in self.active_sessions:
            # Try to load existing session
            try:
                self.memory_manager.load_session(session_id)
                self.active_sessions[session_id] = {
                    "created_at": "restored",
                    "message_count": 0,
                }
            except:
                raise ValueError(
                    f"Session {session_id} not found. Please create a new session."
                )

        # Prepare initial state
        initial_state = {
            "messages": [
                SystemMessage(content=self.system_message),
                HumanMessage(content=user_message),
            ],
            "session_id": session_id,
            "memory": self.memory_manager.load_session(session_id),
            "current_json_state": self.json_manager.load_session_json(session_id),
            "missing_required_fields": [],
            "completion_percentage": 0.0,
            "retries": 0,
        }

        # Create config for this conversation thread
        config = {"configurable": {"thread_id": session_id}}

        # Run the agent
        response = None
        try:
            # Stream the agent's execution
            for event in self.agent.stream(initial_state, config):
                if event:
                    # Extract the last message from the agent
                    if "agent" in event and event["agent"].get("messages"):
                        last_message = event["agent"]["messages"][-1]
                        if isinstance(last_message, AIMessage):
                            response = last_message.content
                    elif "memory" in event:
                        # Memory was updated
                        pass

            # Update session stats
            self.active_sessions[session_id]["message_count"] += 1

        except Exception as e:
            response = f"Désolé, une erreur s'est produite: {str(e)}"
            print(f"Error in chat: {e}")

        return response or "Je n'ai pas pu générer une réponse. Veuillez réessayer."

    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get the current status of a session

        Args:
            session_id: The session identifier

        Returns:
            Status information including progress and missing fields
        """
        try:
            completion = self.json_manager.get_completion_status(session_id)
            validation = self.json_manager.validate_document(session_id)
            memory_stats = self.memory_manager.get_session_stats(session_id)

            return {
                "session_id": session_id,
                "overall_completion": completion["overall_completion"],
                "is_complete": validation["is_complete"],
                "missing_required_count": validation["missing_required_count"],
                "sections": completion["sections"],
                "conversation_turns": memory_stats["total_turns"],
                "duration_minutes": memory_stats["duration_minutes"],
            }
        except Exception as e:
            return {"error": str(e)}

    def export_lease(self, session_id: str, format: str = "json") -> Dict[str, Any]:
        """
        Export the completed lease document

        Args:
            session_id: The session identifier
            format: Export format (json, pdf, docx - only json implemented for now)

        Returns:
            The exported document or status
        """
        try:
            # Validate document is complete
            validation = self.json_manager.validate_document(session_id)

            if not validation["is_complete"]:
                return {
                    "status": "incomplete",
                    "message": f"Document incomplet. Il manque {validation['missing_required_count']} champs obligatoires.",
                    "missing_fields": validation.get("missing_summary", {}),
                }

            # Load the document
            document = self.json_manager.load_session_json(session_id)

            # Remove metadata before export
            export_data = {k: v for k, v in document.items() if not k.startswith("_")}

            if format == "json":
                return {"status": "success", "format": "json", "data": export_data}
            else:
                return {
                    "status": "error",
                    "message": f"Format '{format}' not yet implemented. Use 'json' for now.",
                }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all available sessions"""
        sessions = []

        # List session files
        session_files = list(self.memory_manager.memory_dir.glob("*.json"))

        for session_file in session_files:
            session_id = session_file.stem
            try:
                stats = self.memory_manager.get_session_stats(session_id)
                completion = self.json_manager.get_completion_status(session_id)

                sessions.append(
                    {
                        "session_id": session_id,
                        "completion": completion["overall_percentage"],
                        "turns": stats["total_turns"],
                        "duration_minutes": stats["duration_minutes"],
                    }
                )
            except:
                continue

        return sorted(sessions, key=lambda x: x["session_id"])


# CLI Interface
def main():
    """Command-line interface for the French Lease Assistant"""
    print("=" * 60)
    print("🏠 Assistant de Création de Bail de Location Français")
    print("=" * 60)
    print()

    # Initialize assistant
    assistant = FrenchLeaseAssistant()

    # Session management
    print("Options:")
    print("1. Nouvelle conversation")
    print("2. Reprendre une conversation")
    print("3. Lister les sessions")
    print("4. Quitter")
    print()

    choice = input("Votre choix (1-4): ").strip()

    if choice == "1":
        session_id = assistant.new_session()
        print(f"\n✨ Nouvelle session créée: {session_id[:8]}...")
    elif choice == "2":
        session_id = input("ID de session: ").strip()
        try:
            status = assistant.get_session_status(session_id)
            print(
                f"\n📊 Session restaurée - Complétion: {status['overall_completion']}"
            )
        except:
            print("❌ Session introuvable")
            return
    elif choice == "3":
        sessions = assistant.list_sessions()
        if sessions:
            print("\n📋 Sessions disponibles:")
            for s in sessions:
                print(f"  • {s['session_id'][:8]}... - {s['completion']:.1f}% complété")
        else:
            print("\n❌ Aucune session trouvée")
        return
    elif choice == "4":
        print("Au revoir! 👋")
        return
    else:
        print("❌ Choix invalide")
        return

    # Start conversation
    print("\n" + "=" * 60)
    print("💬 Conversation démarrée")
    print("Tapez 'quit' pour quitter, 'status' pour voir la progression")
    print("=" * 60)
    print()

    # Initial greeting
    response = assistant.chat(
        session_id, "Bonjour, je souhaite créer un bail de location."
    )
    print(f"🤖 Assistant: {response}")
    print()

    # Conversation loop
    while True:
        user_input = input("👤 Vous: ").strip()

        if user_input.lower() == "quit":
            print("\n👋 Conversation terminée")

            # Show final status
            status = assistant.get_session_status(session_id)
            print(f"\n📊 Résumé final:")
            print(f"  • Complétion: {status['overall_completion']}")
            print(f"  • Tours de conversation: {status['conversation_turns']}")
            print(f"  • Durée: {status['duration_minutes']:.1f} minutes")

            if status["is_complete"]:
                print("\n✅ Bail complet! Vous pouvez l'exporter.")
                export = input("Exporter le bail? (o/n): ").strip().lower()
                if export == "o":
                    result = assistant.export_lease(session_id)
                    if result["status"] == "success":
                        # Save to file
                        export_file = f"bail_{session_id[:8]}.json"
                        with open(export_file, "w", encoding="utf-8") as f:
                            json.dump(result["data"], f, ensure_ascii=False, indent=2)
                        print(f"📄 Bail exporté: {export_file}")
            break

        elif user_input.lower() == "status":
            status = assistant.get_session_status(session_id)
            print(f"\n📊 Progression actuelle:")
            print(f"  • Complétion globale: {status['overall_completion']}")
            print(f"  • Champs manquants: {status['missing_required_count']}")
            print("\nPar section:")
            for section, info in status["sections"].items():
                print(
                    f"  • {section}: {info['percentage']:.1f}% ({info['filled']}/{info['total']})"
                )
            print()
            continue

        # Process message
        response = assistant.chat(session_id, user_input)
        print(f"\n🤖 Assistant: {response}")
        print()


if __name__ == "__main__":
    # Check for required environment variables or use defaults
    import dotenv

    dotenv.load_dotenv()

    # Ensure data directories exist
    Path("data").mkdir(exist_ok=True)
    Path("data/sessions").mkdir(exist_ok=True)
    Path("data/memory").mkdir(exist_ok=True)

    # Copy template if not exists
    template_path = Path("data/template_data.json")
    if not template_path.exists():
        # Create from the provided template
        print("Creating template file...")
        # The template content is already provided in the second document
        # We'll save it here
        with open(template_path, "w", encoding="utf-8") as f:
            # Using the template from your second document
            template_content = json.loads(
                open("template_data.json", "r").read()
                if Path("template_data.json").exists()
                else "{}"
            )
            json.dump(template_content, f, ensure_ascii=False, indent=2)

    main()
