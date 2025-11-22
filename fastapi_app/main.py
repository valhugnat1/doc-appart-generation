import sys
import os
import uuid
import time
import json
import glob
from typing import List, Optional, Dict, Any, Union
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_anthropic import ChatAnthropic

# Add the parent directory to sys.path to import agent_recup_info
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
agent_dir = os.path.join(parent_dir, "agent_recup_info")
sys.path.append(agent_dir)

try:
    from agent.graph import create_agent
except ImportError as e:
    print(f"Error importing agent: {e}")
    print(f"sys.path: {sys.path}")
    raise

# Load environment variables
load_dotenv(os.path.join(parent_dir, ".env"))

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Agent Recup Info API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Configuration ---
CONVERSATIONS_DIR = os.path.join(parent_dir, "data", "conversations")
os.makedirs(CONVERSATIONS_DIR, exist_ok=True)

# --- Helper Functions ---

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

# --- Pydantic Models for OpenAI API ---

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "gpt-3.5-turbo" # Default, ignored but kept for compatibility
    messages: List[Message]
    user: Optional[str] = None # Used as session_id
    stream: bool = False # Streaming not implemented yet

class Choice(BaseModel):
    index: int
    message: Message
    finish_reason: str

class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Choice]
    usage: Usage

# --- Agent Initialization ---

# Initialize LLM (Anthropic as per original agent)
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    print("Warning: ANTHROPIC_API_KEY not found in environment variables.")

llm = ChatAnthropic(
    model="claude-sonnet-4-5", 
    api_key=api_key
)

# Create Agent
agent_graph, system_prompt = create_agent(llm)

# --- Endpoints ---

@app.get("/conversations")
async def list_conversations():
    """List all available conversations with metadata, sorted by updated_at desc."""
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
    
    return {"conversations": conversations}

@app.get("/conversations/{uuid}")
async def get_conversation(uuid: str):
    """Get conversation history for a specific UUID."""
    history = load_conversation(uuid)
    # Always return a list of messages for the frontend
    return {"messages": history}

@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest):
    session_id = request.user
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Load existing history
    history = load_conversation(session_id)
    
    # Prepare LangChain messages
    # Start with system prompt
    langchain_messages = [SystemMessage(content=system_prompt)]
    
    # Add history
    for msg in history:
        if msg["role"] == "user":
            langchain_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            langchain_messages.append(AIMessage(content=msg["content"]))
            
    # Add new messages from request (usually just the last one)
    last_user_message = None
    for msg in reversed(request.messages):
        if msg.role == "user":
            last_user_message = msg
            break
            
    if last_user_message:
        langchain_messages.append(HumanMessage(content=last_user_message.content))
        # Update history list for saving later
        history.append({"role": "user", "content": last_user_message.content})
    
    current_state = {
        "messages": langchain_messages,
        "session_id": session_id
    }
    
    print(f"Invoking agent for session: {session_id}")
    
    try:
        # Run the graph
        final_state = agent_graph.invoke(current_state)
        
        # Extract the last message from the agent
        messages = final_state["messages"]
        last_message = messages[-1]
        
        response_content = ""
        if isinstance(last_message, AIMessage):
            response_content = last_message.content
        else:
            response_content = str(last_message)

        # Update history with assistant response
        history.append({"role": "assistant", "content": response_content})
        
        # Save updated conversation
        save_conversation(session_id, history)

        # Construct response
        response = ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4()}",
            created=int(time.time()),
            model=request.model,
            choices=[
                Choice(
                    index=0,
                    message=Message(role="assistant", content=response_content),
                    finish_reason="stop"
                )
            ],
            usage=Usage() 
        )
        
        return response

    except Exception as e:
        print(f"Error invoking agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
