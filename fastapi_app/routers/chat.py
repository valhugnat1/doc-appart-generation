import uuid
import time
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from ..models.chat import ChatCompletionRequest, ChatCompletionResponse, Choice, Message, Usage
from ..services import chat_service, conversation_service

router = APIRouter()

@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest):

    print(request)
    session_id = request.user
    if not session_id:
        session_id = str(uuid.uuid4())
    
    history = conversation_service.load_conversation(session_id)
    
    last_user_message = None
    for msg in reversed(request.messages):
        if msg.role == "user":
            last_user_message = msg
            break
            
    if last_user_message:
        history.append({"role": "user", "content": last_user_message.content})
    
    try:
        if request.stream:
            return StreamingResponse(
                chat_service.stream_chat_request(session_id, history, request.messages, request.model),
                media_type="text/event-stream"
            )
        else:
            response_content = chat_service.process_chat_request(session_id, history, request.messages)
            
            history.append({"role": "assistant", "content": response_content})
            conversation_service.save_conversation(session_id, history)
            chat_service.trigger_bail_generation(session_id)

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
