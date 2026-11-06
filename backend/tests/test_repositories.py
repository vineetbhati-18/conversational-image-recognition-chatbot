import pytest
from uuid import uuid4
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import AsyncSessionLocal
from app.repositories.session_repo import SessionRepository
from app.repositories.image_repo import ImageRepository
from app.repositories.message_repo import MessageRepository


@pytest.mark.asyncio
async def test_repositories_lifecycle():
    async with AsyncSessionLocal() as db:
        # 1. Create Session via Repository
        session = await SessionRepository.create(db, title="Repository Test Session")
        assert session.id is not None
        assert session.title == "Repository Test Session"

        # 2. Add Message via Repository
        msg = await MessageRepository.create(
            db,
            session_id=session.id,
            sender_type="user",
            content="Testing repository pattern message persistence.",
            metadata={"test_tag": "audit"},
        )
        assert msg.id is not None
        assert msg.session_id == session.id

        # 3. Create Image & Detection via Repository
        img = await ImageRepository.create(
            db,
            image_id=uuid4(),
            session_id=session.id,
            filename="repo_test.jpg",
            storage_path="/tmp/repo_test.jpg",
            mime_type="image/jpeg",
            file_size_bytes=1024,
            width=640,
            height=480,
        )
        assert img.filename == "repo_test.jpg"

        # 4. Save Detections
        objs = await ImageRepository.save_detected_objects(
            db,
            image_id=img.id,
            detections=[
                {"class_name": "tank", "confidence": 0.95, "bbox": {"x_min": 10, "y_min": 10, "x_max": 100, "y_max": 100}},
            ],
        )
        assert len(objs) == 1
        assert objs[0].class_name == "tank"

        # 5. Clean up session
        await SessionRepository.delete(db, session)
