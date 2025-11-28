from fastapi import APIRouter, HTTPException
from ..services import conversation_service

router = APIRouter()

@router.get("/conversations")
async def list_conversations():
    """List all available conversations with metadata, sorted by updated_at desc."""
    conversations = conversation_service.list_all_conversations()
    return {"conversations": conversations}

@router.get("/conversations/{uuid}")
async def get_conversation(uuid: str):
    """Get conversation history for a specific UUID."""
    history = conversation_service.load_conversation(uuid)
    # Always return a list of messages for the frontend
    return {"messages": history}
