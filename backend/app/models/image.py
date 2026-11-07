from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from pathlib import Path
from app.core.database import Base


class ImageModel(Base):
    __tablename__ = "images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    storage_path = Column(String(512), nullable=False)
    mime_type = Column(String(64), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("SessionModel", back_populates="images")
    detected_objects = relationship("DetectedObjectModel", back_populates="image", cascade="all, delete-orphan")

    @property
    def url(self) -> str:
        filename = Path(self.storage_path).name if self.storage_path else self.filename
        return f"/uploads/{filename}"


class DetectedObjectModel(Base):
    __tablename__ = "detected_objects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    image_id = Column(UUID(as_uuid=True), ForeignKey("images.id", ondelete="CASCADE"), nullable=False, index=True)
    class_name = Column(String(100), nullable=False)
    confidence_score = Column(Float, nullable=False)
    bbox_x_min = Column(Float, nullable=False)
    bbox_y_min = Column(Float, nullable=False)
    bbox_x_max = Column(Float, nullable=False)
    bbox_y_max = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    image = relationship("ImageModel", back_populates="detected_objects")

    @property
    def confidence(self) -> float:
        return self.confidence_score

    @property
    def bbox(self) -> dict:
        return {
            "x_min": self.bbox_x_min,
            "y_min": self.bbox_y_min,
            "x_max": self.bbox_x_max,
            "y_max": self.bbox_y_max,
        }

    @property
    def normalized_bbox(self) -> dict:
        w = float(self.image.width) if self.image and self.image.width else 1.0
        h = float(self.image.height) if self.image and self.image.height else 1.0
        return {
            "x_min": round(self.bbox_x_min / w, 4),
            "y_min": round(self.bbox_y_min / h, 4),
            "x_max": round(self.bbox_x_max / w, 4),
            "y_max": round(self.bbox_y_max / h, 4),
        }

    @property
    def bbox(self) -> dict:
        return {
            "x_min": self.bbox_x_min,
            "y_min": self.bbox_y_min,
            "x_max": self.bbox_x_max,
            "y_max": self.bbox_y_max,
        }

