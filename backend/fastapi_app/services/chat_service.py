import os
import sys
import uuid
import time
import json
from typing import List, Dict, Any, AsyncGenerator
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv

from ..models.chat import Delta, StreamChoice, ChatCompletionStreamResponse, ToolCall, Function
from ..config import PARENT_DIR
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

async def stream_chat_request(session_id: str, history: List[Dict[str, Any]], new_messages: List[Any], model_name: str) -> AsyncGenerator[str, None]:
    """
    Stream a chat request using the agent graph.
    Yields SSE formatted chunks.
    """
    response_id = f"chatcmpl-{uuid.uuid4()}"
    created_time = int(time.time())

    # Prepare LangChain messages (same logic as process_chat_request)
    system_prompt_with_session = f"{system_prompt}\n\nCURRENT SESSION ID: {session_id}"
    langchain_messages = [SystemMessage(content=system_prompt_with_session)]
    
    for msg in history:
        if msg["role"] == "user":
            langchain_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            langchain_messages.append(AIMessage(content=msg["content"]))
            
    last_user_message = None
    for msg in reversed(new_messages):
        if msg.role == "user":
            last_user_message = msg
            break
            
    if last_user_message:
        langchain_messages.append(HumanMessage(content=last_user_message.content))
    
    current_state = {
        "messages": langchain_messages,
        "session_id": session_id
    }
    
    print(f"Streaming agent for session: {session_id}")

    # Initial chunk
    delta = Delta(role="assistant", content="")
    choice = StreamChoice(index=0, delta=delta, finish_reason=None)
    chunk = ChatCompletionStreamResponse(
        id=response_id, created=created_time, model=model_name, choices=[choice]
    )
    yield f"data: {chunk.model_dump_json()}\n\n"

    full_response_content = ""

    try:
        async for event in agent_graph.astream(current_state, stream_mode="messages"):
            message_chunk = event[0] if isinstance(event, tuple) else event

            print(message_chunk)
            
            # We are interested in AIMessageChunks that have content
            if isinstance(message_chunk, AIMessage) and message_chunk.content:
                content = message_chunk.content
                text_content = ""
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            text_content += item.get("text", "")
                elif isinstance(content, str):
                    text_content = content
                
                if text_content:
                    full_response_content += text_content
                    
                    delta = Delta(content=text_content)
                    choice = StreamChoice(index=0, delta=delta, finish_reason=None)
                    chunk = ChatCompletionStreamResponse(
                        id=response_id, created=created_time, model=model_name, choices=[choice]
                    )
                    yield f"data: {chunk.model_dump_json()}\n\n"

            # Handle tool call chunks
            if hasattr(message_chunk, 'tool_call_chunks') and message_chunk.tool_call_chunks:
                tool_calls = []
                for tc_chunk in message_chunk.tool_call_chunks:
                    # Check if tc_chunk is a dict or object
                    if isinstance(tc_chunk, dict):
                        index = tc_chunk.get("index")
                        tc_id = tc_chunk.get("id")
                        name = tc_chunk.get("name")
                        args = tc_chunk.get("args")
                    else:
                        index = tc_chunk.index
                        tc_id = tc_chunk.id
                        name = tc_chunk.name
                        args = tc_chunk.args

                    tool_calls.append(ToolCall(
                        index=index,
                        id=tc_id,
                        type="function",
                        function=Function(
                            name=name,
                            arguments=args
                        )
                    ))
                
                delta = Delta(tool_calls=tool_calls)
                choice = StreamChoice(index=0, delta=delta, finish_reason=None)
                chunk = ChatCompletionStreamResponse(
                    id=response_id, created=created_time, model=model_name, choices=[choice]
                )
                yield f"data: {chunk.model_dump_json()}\n\n"
                
    except Exception as e:
        print(f"Error during streaming: {e}")

    delta = Delta()
    choice = StreamChoice(index=0, delta=delta, finish_reason="stop")
    chunk = ChatCompletionStreamResponse(
        id=response_id, created=created_time, model=model_name, choices=[choice]
    )
    yield f"data: {chunk.model_dump_json()}\n\n"
    yield "data: [DONE]\n\n"

    from . import conversation_service 
    
    history.append({"role": "assistant", "content": full_response_content})
    conversation_service.save_conversation(session_id, history)
    
    trigger_bail_generation(session_id)
