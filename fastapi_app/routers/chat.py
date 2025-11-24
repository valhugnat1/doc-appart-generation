import uuid
import time
from fastapi import APIRouter, HTTPException
from ..models.chat import ChatCompletionRequest, ChatCompletionResponse, Choice, Message, Usage
from ..services import chat_service, conversation_service

router = APIRouter()

@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest):
    session_id = request.user
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Load existing history
    history = conversation_service.load_conversation(session_id)
    
    # Update history with user message
    last_user_message = None
    for msg in reversed(request.messages):
        if msg.role == "user":
            last_user_message = msg
            break
            
    if last_user_message:
        history.append({"role": "user", "content": last_user_message.content})
    
    try:
        # Process chat request
        response_content = chat_service.process_chat_request(session_id, history, request.messages)
        
        # Update history with assistant response
        history.append({"role": "assistant", "content": response_content})
        
        # Save updated conversation
        conversation_service.save_conversation(session_id, history)

        # Generate bail
        chat_service.trigger_bail_generation(session_id)

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
