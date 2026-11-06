from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from app.schemas.chat import MessageResponse
from app.schemas.image import ImageResponse


class SessionBase(BaseModel):
    title: str = Field(default="New Conversation", max_length=255)


class SessionCreate(BaseModel):
    title: Optional[str] = Field(default="New Conversation", max_length=255)


class SessionUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)


class SessionResponse(SessionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


class SessionDetailResponse(SessionResponse):
    messages: List[MessageResponse] = []
    images: List[ImageResponse] = []

    model_config = ConfigDict(from_attributes=True)


SessionDetailResponse.model_rebuild()
