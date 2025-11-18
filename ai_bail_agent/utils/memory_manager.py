"""
Memory Manager for conversation persistence
"""

import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import uuid


class MemoryManager:
    """Manages conversation memory and session state"""

    def __init__(self, memory_dir: str = "data/memory"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self._active_sessions = {}

    def create_session(self) -> str:
        """Create a new conversation session"""
        session_id = str(uuid.uuid4())

        memory = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "current_topic": None,
            "last_asked_fields": [],
            "conversation_history": [],
            "collected_information": {},
            "context": {
                "user_prefers_short_answers": False,
                "language": "fr",
                "completion_milestones": [],
            },
        }

        # Save to file
        memory_file = self.memory_dir / f"{session_id}.json"
        with open(memory_file, "w", encoding="utf-8") as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)

        self._active_sessions[session_id] = memory
        return session_id

    def load_session(self, session_id: str) -> Dict[str, Any]:
        """Load an existing session from disk"""
        if session_id in self._active_sessions:
            return self._active_sessions[session_id]

        memory_file = self.memory_dir / f"{session_id}.json"
        if not memory_file.exists():
            raise ValueError(f"Session {session_id} not found")

        with open(memory_file, "r", encoding="utf-8") as f:
            memory = json.load(f)

        self._active_sessions[session_id] = memory
        return memory

    def save_session(self, session_id: str, memory: Dict[str, Any]):
        """Save session to disk"""
        memory["last_activity"] = datetime.now().isoformat()

        memory_file = self.memory_dir / f"{session_id}.json"
        with open(memory_file, "w", encoding="utf-8") as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)

        self._active_sessions[session_id] = memory

    def add_conversation_turn(
        self,
        session_id: str,
        user_message: str,
        assistant_response: str,
        extracted_info: Dict[str, Any] = None,
    ):
        """Add a conversation turn to memory"""
        memory = self.load_session(session_id)

        turn = {
            "timestamp": datetime.now().isoformat(),
            "user": user_message,
            "assistant": assistant_response,
            "extracted_info": extracted_info or {},
        }

        memory["conversation_history"].append(turn)

        # Update collected information
        if extracted_info:
            memory["collected_information"].update(extracted_info)

        self.save_session(session_id, memory)

    def update_context(self, session_id: str, context_updates: Dict[str, Any]):
        """Update session context"""
        memory = self.load_session(session_id)
        memory["context"].update(context_updates)
        self.save_session(session_id, memory)

    def set_current_topic(self, session_id: str, topic: str):
        """Set the current conversation topic"""
        memory = self.load_session(session_id)
        memory["current_topic"] = topic
        self.save_session(session_id, memory)

    def add_asked_fields(self, session_id: str, fields: List[str]):
        """Track which fields have been asked about"""
        memory = self.load_session(session_id)
        memory["last_asked_fields"] = fields
        self.save_session(session_id, memory)

    def get_conversation_summary(self, session_id: str) -> str:
        """Generate a summary of the conversation so far"""
        memory = self.load_session(session_id)

        if not memory["conversation_history"]:
            return "Nouvelle conversation"

        # Get last 5 turns for context
        recent_turns = memory["conversation_history"][-5:]
        summary_parts = []

        for turn in recent_turns:
            if turn.get("extracted_info"):
                info_str = ", ".join(
                    f"{k}={v}" for k, v in turn["extracted_info"].items()
                )
                summary_parts.append(f"Collecté: {info_str}")

        if memory["current_topic"]:
            summary_parts.insert(0, f"Sujet actuel: {memory['current_topic']}")

        return " | ".join(summary_parts) if summary_parts else "Conversation en cours"

    def get_unanswered_questions(self, session_id: str) -> List[str]:
        """Get questions that were asked but not answered"""
        memory = self.load_session(session_id)

        unanswered = []
        for i, turn in enumerate(memory["conversation_history"]):
            # Check if assistant asked questions
            if "?" in turn.get("assistant", ""):
                # Check if next user message answered them
                if i + 1 < len(memory["conversation_history"]):
                    next_turn = memory["conversation_history"][i + 1]
                    if not next_turn.get("extracted_info"):
                        # Question might not have been answered
                        questions = [
                            q.strip() for q in turn["assistant"].split("?") if q.strip()
                        ]
                        unanswered.extend(questions)

        return unanswered[-3:]  # Return last 3 unanswered questions

    def should_ask_for_confirmation(self, session_id: str) -> bool:
        """Determine if we should ask for confirmation based on collected info"""
        memory = self.load_session(session_id)

        # Ask for confirmation every 10 pieces of information
        info_count = len(memory["collected_information"])
        return info_count > 0 and info_count % 10 == 0

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics about the session"""
        memory = self.load_session(session_id)

        return {
            "session_id": session_id,
            "duration_minutes": self._calculate_duration(memory),
            "total_turns": len(memory["conversation_history"]),
            "fields_collected": len(memory["collected_information"]),
            "current_topic": memory.get("current_topic"),
            "language": memory["context"].get("language", "fr"),
        }

    def _calculate_duration(self, memory: Dict[str, Any]) -> float:
        """Calculate session duration in minutes"""
        try:
            created = datetime.fromisoformat(memory["created_at"])
            last_activity = datetime.fromisoformat(memory["last_activity"])
            return (last_activity - created).total_seconds() / 60
        except:
            return 0.0

    def cleanup_old_sessions(self, days: int = 7):
        """Remove sessions older than specified days"""
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)

        for memory_file in self.memory_dir.glob("*.json"):
            if memory_file.stat().st_mtime < cutoff:
                memory_file.unlink()
                session_id = memory_file.stem
                if session_id in self._active_sessions:
                    del self._active_sessions[session_id]
