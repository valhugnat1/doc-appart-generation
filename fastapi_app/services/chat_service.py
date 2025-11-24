import os
import sys
import uuid
import time
from typing import List, Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv

from ..config import PARENT_DIR
# Import config to ensure sys.path is set up
from .. import config 

# Load environment variables
load_dotenv(os.path.join(PARENT_DIR, ".env"))

# Initialize LLM and Agent
try:
    from agent.graph import create_agent
except ImportError as e:
    print(f"Error importing agent: {e}")
    print(f"sys.path: {sys.path}")
    raise

try:
    from generate_bail import generate_bail_for_session
except ImportError as e:
    print(f"Error importing generate_bail: {e}")
    # We don't raise here to allow the app to start even if bail generation fails to import
    pass

api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    print("Warning: ANTHROPIC_API_KEY not found in environment variables.")

llm = ChatAnthropic(
    model="claude-sonnet-4-5", 
    api_key=api_key
)

agent_graph, system_prompt = create_agent(llm)

def process_chat_request(session_id: str, history: List[Dict[str, Any]], new_messages: List[Any]) -> str:
    """
    Process a chat request using the agent graph.
    Returns the response content.
    """
    # Prepare LangChain messages
    # Start with system prompt
    # Inject session_id into the system prompt so the agent knows it
    system_prompt_with_session = f"{system_prompt}\n\nCURRENT SESSION ID: {session_id}"
    langchain_messages = [SystemMessage(content=system_prompt_with_session)]
    
    # Add history
    for msg in history:
        if msg["role"] == "user":
            langchain_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            langchain_messages.append(AIMessage(content=msg["content"]))
            
    # Add new messages from request (usually just the last one)
    last_user_message = None
    for msg in reversed(new_messages):
        if msg.role == "user":
            last_user_message = msg
            break
            
    if last_user_message:
        langchain_messages.append(HumanMessage(content=last_user_message.content))
        # Update history list for saving later (caller handles saving, but we need to return the response)
    
    current_state = {
        "messages": langchain_messages,
        "session_id": session_id
    }
    
    print(f"Invoking agent for session: {session_id}")
    
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

    return response_content

def trigger_bail_generation(session_id: str):
    print(f"Generating bail for session: {session_id}")
    try:
        generate_bail_for_session(session_id)
    except Exception as e:
        print(f"Error generating bail: {e}")
