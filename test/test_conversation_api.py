import requests
import uuid
import json
import sys

BASE_URL = "http://localhost:8000"

def test_conversation_flow():
    print("--- Testing Conversation Flow ---")
    
    # 1. List conversations (should be empty or have existing)
    print("\n1. Listing conversations...")
    try:
        resp = requests.get(f"{BASE_URL}/conversations")
        resp.raise_for_status()
        initial_convs = resp.json()["conversations"]
        print(f"Initial conversations: {initial_convs}")
    except Exception as e:
        print(f"Failed to list conversations: {e}")
        return

    # 2. Start a new chat with a specific UUID
    test_uuid = str(uuid.uuid4())
    print(f"\n2. Starting chat with UUID: {test_uuid}")
    
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": "Hello, this is a test message to save."}
        ],
        "user": test_uuid
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/v1/chat/completions", json=payload)
        resp.raise_for_status()
        result = resp.json()
        print(f"Chat response: {result['choices'][0]['message']['content']}")
    except Exception as e:
        print(f"Failed to send chat message: {e}")
        return

    # 3. List conversations again (should include new UUID)
    print("\n3. Listing conversations again...")
    try:
        resp = requests.get(f"{BASE_URL}/conversations")
        resp.raise_for_status()
        new_convs = resp.json()["conversations"]
        print(f"New conversations: {new_convs}")
        if test_uuid in new_convs:
            print("SUCCESS: New UUID found in list.")
        else:
            print("FAILURE: New UUID NOT found in list.")
    except Exception as e:
        print(f"Failed to list conversations: {e}")
        return

    # 4. Get conversation history
    print(f"\n4. Getting history for {test_uuid}...")
    try:
        resp = requests.get(f"{BASE_URL}/conversations/{test_uuid}")
        resp.raise_for_status()
        history = resp.json()["messages"]
        print(f"History length: {len(history)}")
        print(f"History content: {json.dumps(history, indent=2)}")
        
        if len(history) >= 2:
             print("SUCCESS: History contains at least user message and assistant response.")
        else:
             print("FAILURE: History incomplete.")
             
    except Exception as e:
        print(f"Failed to get history: {e}")
        return

if __name__ == "__main__":
    test_conversation_flow()
