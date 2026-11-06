import pytest
from httpx import AsyncClient, ASGITransport
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import app


@pytest.mark.asyncio
async def test_session_lifecycle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create a session
        create_res = await client.post("/api/v1/sessions", json={"title": "Recon Test Session Alpha"})
        assert create_res.status_code == 201
        session_data = create_res.json()
        session_id = session_data["id"]
        assert session_data["title"] == "Recon Test Session Alpha"

        # 2. List sessions
        list_res = await client.get("/api/v1/sessions")
        assert list_res.status_code == 200
        sessions = list_res.json()
        assert any(s["id"] == session_id for s in sessions)

        # 3. Get session detail
        detail_res = await client.get(f"/api/v1/sessions/{session_id}")
        assert detail_res.status_code == 200
        detail = detail_res.json()
        assert detail["id"] == session_id
        assert "messages" in detail

        # 4. Delete session
        del_res = await client.delete(f"/api/v1/sessions/{session_id}")
        assert del_res.status_code == 204

        # 5. Verify deleted
        get_deleted = await client.get(f"/api/v1/sessions/{session_id}")
        assert get_deleted.status_code == 404
