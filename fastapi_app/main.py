import sys
import os
import uuid
import time
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

@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest):
    session_id = request.user
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Convert OpenAI messages to LangChain messages
    # We only take the last user message for the current turn, 
    # as the agent graph manages history in its state (if persisted).
    # However, the current agent implementation in main.py keeps history in memory.
    # The graph.py implementation expects 'messages' in state.
    # Since we don't have a persistent store connected to the graph in this simple setup,
    # we might need to reconstruct history or rely on the client sending full history.
    # But the agent graph is stateful if we use a checkpointer. 
    # The current graph.py DOES NOT use a checkpointer, so it's stateless between invokes unless we pass the full history.
    
    # Strategy: Pass the full history from the request to the agent.
    langchain_messages = [SystemMessage(content=system_prompt)]
    
    for msg in request.messages:
        if msg.role == "user":
            langchain_messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            langchain_messages.append(AIMessage(content=msg.content))
        elif msg.role == "system":
            # We already added the main system prompt, but if client sends one, maybe ignore or append?
            # Let's ignore client system messages to enforce our agent's persona
            pass
            
    # Add session_id to the last message or state if needed by tools
    # The tools tool.py implementation doesn't seem to automatically extract session_id from state
    # unless the agent passes it.
    # The system prompt tells the agent: "You will be provided with a session_id. ALWAYS use this ID for tool calls."
    # So we should inject it into the context.
    
    # Let's append a hidden system message or modify the last user message to include session_id
    # if it's not already there.
    # A cleaner way is to trust the agent to use the session_id provided in the state if we pass it.
    
    current_state = {
        "messages": langchain_messages,
        "session_id": session_id
    }
    
    # Invoke the agent
    # We use invoke instead of stream for the non-streaming endpoint
    # The graph returns the final state.
    
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
            # Fallback if the last message isn't an AI message (unlikely)
            response_content = str(last_message)

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
            usage=Usage() # Usage tracking not implemented
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
