import pytest
from uuid import uuid4
from httpx import AsyncClient, ASGITransport
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import app


@pytest.mark.asyncio
async def test_chat_message_without_image():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        session_id = str(uuid4())
        payload = {
            "session_id": session_id,
            "content": "Hello, how does this conversational recognition system work?",
        }
        res = await client.post("/api/v1/chat/message", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["sender_type"] == "assistant"
        assert len(data["content"]) > 0
        assert "latency_ms" in data["metadata"]
