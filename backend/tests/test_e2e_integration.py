import pytest
import io
from PIL import Image
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import app


def generate_recon_sample_image() -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", (640, 480), color=(70, 90, 60))
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.mark.asyncio
async def test_full_multimodal_e2e_pipeline():
    transport = ASGITransport(app=app)

    # Mock BLIP service answer_question to avoid multi-gigabyte downloads during fast test execution
    mock_blip = MagicMock()
    mock_blip.answer_question.return_value = {
        "question": "What objects or equipment do you observe in this image?",
        "answer": "military vehicle",
        "latency_ms": 28.5,
        "device": "mps",
        "model": "Salesforce/blip-vqa-base",
    }

    with patch("app.api.v1.chat.get_blip_service", return_value=mock_blip):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Create a new conversation session
            session_res = await client.post("/api/v1/sessions", json={"title": "BEL Tactical E2E Surveillance"})
            assert session_res.status_code == 201
            session_id = session_res.json()["id"]

            # 2. Upload an image to the session (triggers real YOLO detection pass)
            img_bytes = generate_recon_sample_image()
            files = {"file": ("tactical_surveillance.jpg", img_bytes, "image/jpeg")}
            upload_res = await client.post(
                "/api/v1/images/upload",
                files=files,
                data={"session_id": session_id},
            )
            assert upload_res.status_code == 201
            upload_data = upload_res.json()
            image_id = upload_data["id"]
            assert upload_data["session_id"] == session_id
            assert upload_data["width"] == 640
            assert upload_data["height"] == 480

            # 3. First dialogue turn: Ask about objects
            q1_res = await client.post(
                "/api/v1/chat/message",
                json={
                    "session_id": session_id,
                    "image_id": image_id,
                    "content": "What objects or equipment do you observe in this image?",
                },
            )
            assert q1_res.status_code == 200
            q1_data = q1_res.json()
            assert q1_data["sender_type"] == "assistant"
            assert len(q1_data["content"]) > 0

            # 4. Second dialogue turn: Multi-turn follow-up with pronoun resolution
            q2_res = await client.post(
                "/api/v1/chat/message",
                json={
                    "session_id": session_id,
                    "image_id": image_id,
                    "content": "Where is it located?",
                },
            )
            assert q2_res.status_code == 200
            q2_data = q2_res.json()
            assert q2_data["sender_type"] == "assistant"

            # 5. Fetch full session details with messages and images
            detail_res = await client.get(f"/api/v1/sessions/{session_id}")
            assert detail_res.status_code == 200
            detail = detail_res.json()
            assert len(detail["messages"]) >= 4  # 2 user turns + 2 assistant turns
            assert len(detail["images"]) >= 1

            # 6. Cleanup
            del_res = await client.delete(f"/api/v1/sessions/{session_id}")
            assert del_res.status_code == 204
