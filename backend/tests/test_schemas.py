import pytest
from uuid import uuid4
from datetime import datetime
from pydantic import ValidationError
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.schemas.session import SessionCreate, SessionResponse
from app.schemas.image import BoundingBox, DetectedObjectSchema, ImageResponse
from app.schemas.chat import ChatMessageRequest, MessageResponse


def test_session_schemas():
    # Valid creation
    s = SessionCreate(title="Test Recon Session")
    assert s.title == "Test Recon Session"

    # Default title
    s_default = SessionCreate()
    assert s_default.title == "New Conversation"

    # Valid response
    res = SessionResponse(
        id=uuid4(),
        title="Test Session",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        message_count=5,
    )
    assert res.message_count == 5


def test_image_bounding_box_schemas():
    bbox = BoundingBox(x_min=10.5, y_min=20.0, x_max=100.2, y_max=150.8)
    assert bbox.x_max == 100.2

    obj = DetectedObjectSchema(
        id=uuid4(),
        class_name="truck",
        confidence=0.952,
        bbox=bbox,
    )
    assert obj.confidence == 0.952

    # Confidence must be between 0 and 1
    with pytest.raises(ValidationError):
        DetectedObjectSchema(
            id=uuid4(),
            class_name="truck",
            confidence=1.5,
            bbox=bbox,
        )


def test_chat_schemas():
    req = ChatMessageRequest(
        session_id=uuid4(),
        content="What objects are in the foreground?",
        image_id=uuid4(),
    )
    assert "foreground" in req.content

    # Empty content rejected
    with pytest.raises(ValidationError):
        ChatMessageRequest(session_id=uuid4(), content="")
