import uvicorn
import json
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from agent import app  # We only need the app from agent now
from langchain_core.messages import HumanMessage

api = FastAPI(title="Agent Contract de Location")

# Store state in memory for simplicity (Use Redis/Postgres for production)
# Key: thread_id, Value: State Snapshot
memory_store = {}
TEMPLATE_FILE = "contrat_data.json"


class ChatRequest(BaseModel):
    thread_id: str
    message: str = None  # Optional, null on first request to start


class ChatResponse(BaseModel):
    response: str
    is_complete: bool
    current_json_state: Dict[str, Any]


def load_template():
    """Helper to load the JSON template from disk."""
    if not os.path.exists(TEMPLATE_FILE):
        raise HTTPException(
            status_code=500,
            detail=f"Template file '{TEMPLATE_FILE}' not found. Please ensure it exists in the root directory.",
        )

    try:
        with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail=f"Error decoding '{TEMPLATE_FILE}'. Please check JSON format.",
        )


@api.post("/chat/completion", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    config = {"configurable": {"thread_id": req.thread_id}}

    # 1. Initialize state if new thread
    if req.thread_id not in memory_store:

        # Load the template from file
        template_data = load_template()

        # Initialize state
        initial_state = {
            "messages": [],
            "contract_data": template_data,  # Populated from file
            "completed": False,
            "current_field_info": None,
        }

        # If user sent a message to start (unlikely but possible), add it
        if req.message:
            initial_state["messages"].append(HumanMessage(content=req.message))

        # Run the graph
        final_state = app.invoke(initial_state, config=config)
        memory_store[req.thread_id] = final_state

    else:
        # 2. Continue existing conversation
        current_state = memory_store[req.thread_id]

        if req.message:
            # Update state with new user message
            inputs = {"messages": [HumanMessage(content=req.message)]}

            # Resume graph execution
            # We pass the current contract_data to ensure it persists (and doesn't reset to the file template)
            inputs["contract_data"] = current_state["contract_data"]
            inputs["current_field_info"] = current_state.get("current_field_info")

            final_state = app.invoke(inputs, config=config)
            memory_store[req.thread_id] = final_state
        else:
            # Just checking status or restarting an interrupted flow
            final_state = current_state

    # Extract the last AI message to send back
    last_message = (
        final_state["messages"][-1].content if final_state["messages"] else ""
    )

    return ChatResponse(
        response=last_message,
        is_complete=final_state.get("completed", False),
        current_json_state=final_state.get("contract_data", {}),
    )


if __name__ == "__main__":
    uvicorn.run(api, host="0.0.0.0", port=8000)
