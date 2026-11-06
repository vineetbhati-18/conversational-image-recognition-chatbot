from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, List


class BoundingBox(BaseModel):
    x_min: float = Field(..., description="Top-left X coordinate")
    y_min: float = Field(..., description="Top-left Y coordinate")
    x_max: float = Field(..., description="Bottom-right X coordinate")
    y_max: float = Field(..., description="Bottom-right Y coordinate")


class DetectedObjectSchema(BaseModel):
    id: UUID
    class_name: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: BoundingBox

    model_config = ConfigDict(from_attributes=True)


class DetectionRequest(BaseModel):
    confidence_threshold: float = Field(default=0.35, ge=0.05, le=0.99)


class ImageResponse(BaseModel):
    id: UUID
    session_id: UUID
    filename: str
    file_size_bytes: int
    width: int
    height: int
    mime_type: str
    url: str
    detected_objects: List[DetectedObjectSchema] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
