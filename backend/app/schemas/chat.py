from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any, Literal


class ChatMessageRequest(BaseModel):
    session_id: UUID = Field(..., description="Target conversation session UUID")
    content: str = Field(..., min_length=1, max_length=4000, description="User question or prompt")
    image_id: Optional[UUID] = Field(default=None, description="Active image context UUID if available")


class MessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    image_id: Optional[UUID] = None
    sender_type: Literal["user", "assistant", "system"]
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatCompletionResponse(BaseModel):
    message: MessageResponse
    detected_classes: Optional[list] = []
    vqa_answer: Optional[str] = None
    latency_ms: Optional[float] = None
