import requests
import json
import sys
import time

def test_chat_completion():
    url = "http://127.0.0.1:8000/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": "Bonjour, je voudrais remplir mon bail."}
        ],
        "user": "test-session-123"
    }

    print(f"Sending request to {url}...")
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Response JSON:")
            print(json.dumps(response.json(), indent=2))
            return True
        else:
            print("Error Response:")
            print(response.text)
            return False
    except requests.exceptions.ConnectionError:
        print("Connection refused. Is the server running?")
        return False

if __name__ == "__main__":
    # Wait a bit for server to start if run immediately after
    time.sleep(2)
    if test_chat_completion():
        print("Test PASSED")
        sys.exit(0)
    else:
        print("Test FAILED")
        sys.exit(1)
