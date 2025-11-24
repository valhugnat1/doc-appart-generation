import os
import json
import time
import glob
from typing import List, Dict, Any
from ..config import CONVERSATIONS_DIR

def get_conversation_path(session_id: str) -> str:
    return os.path.join(CONVERSATIONS_DIR, f"{session_id}.json")

def save_conversation(session_id: str, messages: List[Dict[str, Any]]):
    file_path = get_conversation_path(session_id)
    
    current_time = time.time()
    data = {
        "id": session_id,
        "updated_at": current_time,
        "messages": messages
    }
    
    # Try to preserve created_at if file exists
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                # Handle legacy format (list of messages)
                if isinstance(existing_data, list):
                    data["created_at"] = os.path.getctime(file_path)
                else:
                    data["created_at"] = existing_data.get("created_at", current_time)
        except Exception:
            data["created_at"] = current_time
    else:
        data["created_at"] = current_time

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_conversation(session_id: str) -> List[Dict[str, Any]]:
    file_path = get_conversation_path(session_id)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return data.get("messages", [])
    return []

def list_all_conversations() -> List[Dict[str, Any]]:
    files = glob.glob(os.path.join(CONVERSATIONS_DIR, "*.json"))
    conversations = []
    
    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as file:
                data = json.load(file)
                
            uuid = os.path.splitext(os.path.basename(f))[0]
            
            # Handle legacy format
            if isinstance(data, list):
                updated_at = os.path.getmtime(f)
                created_at = os.path.getctime(f)
                # Try to get a title from the first message
                title = "New Conversation"
                if data and len(data) > 0:
                    title = data[0].get("content", "")[:30] + "..."
            else:
                updated_at = data.get("updated_at", os.path.getmtime(f))
                created_at = data.get("created_at", os.path.getctime(f))
                messages = data.get("messages", [])
                title = "New Conversation"
                if messages and len(messages) > 0:
                    title = messages[0].get("content", "")[:30] + "..."
            
            conversations.append({
                "id": uuid,
                "updated_at": updated_at,
                "created_at": created_at,
                "title": title
            })
        except Exception as e:
            print(f"Error reading conversation file {f}: {e}")
            continue
            
    # Sort by updated_at descending
    conversations.sort(key=lambda x: x["updated_at"], reverse=True)
    return conversations
