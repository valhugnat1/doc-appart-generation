from typing import List, Optional
from pydantic import BaseModel

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "gpt-3.5-turbo" # Default, ignored but kept for compatibility
    messages: List[Message]
    user: Optional[str] = None # Used as session_id
    stream: bool = False 

class Choice(BaseModel):
    index: int
    message: Message
    finish_reason: Optional[str] = None

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
    usage: Optional[Usage] = None

# Streaming models
class Function(BaseModel):
    name: Optional[str] = None
    arguments: Optional[str] = None

class ToolCall(BaseModel):
    index: int
    id: Optional[str] = None
    type: Optional[str] = None
    function: Optional[Function] = None

class Delta(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None

class StreamChoice(BaseModel):
    index: int
    delta: Delta
    finish_reason: Optional[str] = None

class ChatCompletionStreamResponse(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[StreamChoice]
