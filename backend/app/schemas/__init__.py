"""
Pydantic Schemas Package for Request and Response validation.
"""
from app.schemas.session import SessionCreate, SessionUpdate, SessionResponse, SessionDetailResponse
from app.schemas.image import BoundingBox, DetectedObjectSchema, ImageResponse, DetectionRequest
from app.schemas.chat import ChatMessageRequest, MessageResponse, ChatCompletionResponse

__all__ = [
    "SessionCreate",
    "SessionUpdate",
    "SessionResponse",
    "SessionDetailResponse",
    "BoundingBox",
    "DetectedObjectSchema",
    "ImageResponse",
    "DetectionRequest",
    "ChatMessageRequest",
    "MessageResponse",
    "ChatCompletionResponse",
]
