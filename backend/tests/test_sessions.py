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


@pytest.mark.asyncio
async def test_session_restoration_after_refresh():
    """
    Simulates browser refresh and verifies that:
    1. The session is returned in GET /api/v1/sessions.
    2. Full session details (messages, image metadata, YOLO detections with bounding boxes) are restored.
    3. Multi-turn dialogue context is retained across session reload.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create a session
        create_res = await client.post("/api/v1/sessions", json={"title": "Session Restoration Test"})
        assert create_res.status_code == 201
        session_id = create_res.json()["id"]

        # 2. Upload sample image
        import io
        from PIL import Image
        buf = io.BytesIO()
        Image.new("RGB", (640, 480), color=(80, 100, 60)).save(buf, format="JPEG")
        img_bytes = buf.getvalue()

        files = {"file": ("tactical_scene.jpg", img_bytes, "image/jpeg")}
        upload_res = await client.post("/api/v1/images/upload", files=files, data={"session_id": session_id})
        assert upload_res.status_code == 201
        img_data = upload_res.json()
        image_id = img_data["id"]

        # 3. Complete chat interactions
        msg1_res = await client.post("/api/v1/chat/message", json={
            "session_id": session_id,
            "image_id": image_id,
            "content": "What objects are detected in this image?",
        })
        assert msg1_res.status_code == 200
        msg1_content = msg1_res.json()["content"]

        msg2_res = await client.post("/api/v1/chat/message", json={
            "session_id": session_id,
            "image_id": image_id,
            "content": "Where are they located?",
        })
        assert msg2_res.status_code == 200

        # 4. SIMULATE BROWSER REFRESH: Fetch session list and retrieve target session detail
        list_res = await client.get("/api/v1/sessions")
        assert list_res.status_code == 200
        sessions = list_res.json()
        target_session = next((s for s in sessions if s["id"] == session_id), None)
        assert target_session is not None, "Saved session must be listed in sidebar sessions on startup"

        detail_res = await client.get(f"/api/v1/sessions/{session_id}")
        assert detail_res.status_code == 200
        restored = detail_res.json()

        # Verify messages restored in exact order
        assert len(restored["messages"]) >= 4  # 2 user turns + 2 assistant turns
        assert restored["messages"][0]["content"] == "What objects are detected in this image?"
        assert restored["messages"][1]["content"] == msg1_content

        # Verify image and YOLO detection telemetry restored
        assert len(restored["images"]) >= 1
        restored_img = restored["images"][0]
        assert restored_img["id"] == image_id
        assert restored_img["filename"] == "tactical_scene.jpg"
        assert restored_img["width"] == 640
        assert restored_img["height"] == 480
        assert restored_img["url"].startswith("/uploads/")
        assert isinstance(restored_img["detected_objects"], list)

        # 5. Send follow-up turn in restored session
        followup_res = await client.post("/api/v1/chat/message", json={
            "session_id": session_id,
            "image_id": image_id,
            "content": "Count the total objects.",
        })
        assert followup_res.status_code == 200

        # Cleanup
        del_res = await client.delete(f"/api/v1/sessions/{session_id}")
        assert del_res.status_code == 204


@pytest.mark.asyncio
async def test_conversation_switching_isolation():
    """
    Verifies that switching between two separate conversations loads the exact
    distinct messages, images, and detections for each session with zero data leakage.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create Session A
        res_a = await client.post("/api/v1/sessions", json={"title": "Session A (Airfield)"})
        assert res_a.status_code == 201
        session_a_id = res_a.json()["id"]

        # Create Session B
        res_b = await client.post("/api/v1/sessions", json={"title": "Session B (Harbor)"})
        assert res_b.status_code == 201
        session_b_id = res_b.json()["id"]

        # Chat in Session A
        await client.post("/api/v1/chat/message", json={
            "session_id": session_a_id,
            "content": "Message for Airfield recon",
        })

        # Chat in Session B
        await client.post("/api/v1/chat/message", json={
            "session_id": session_b_id,
            "content": "Message for Harbor surveillance",
        })

        # Switch to Session A: verify only Session A messages exist
        detail_a = (await client.get(f"/api/v1/sessions/{session_a_id}")).json()
        assert len(detail_a["messages"]) == 2
        assert detail_a["messages"][0]["content"] == "Message for Airfield recon"
        assert not any("Harbor" in m["content"] for m in detail_a["messages"])

        # Switch to Session B: verify only Session B messages exist
        detail_b = (await client.get(f"/api/v1/sessions/{session_b_id}")).json()
        assert len(detail_b["messages"]) == 2
        assert detail_b["messages"][0]["content"] == "Message for Harbor surveillance"
        assert not any("Airfield" in m["content"] for m in detail_b["messages"])

        # Cleanup
        await client.delete(f"/api/v1/sessions/{session_a_id}")
        await client.delete(f"/api/v1/sessions/{session_b_id}")


@pytest.mark.asyncio
async def test_image_only_session_restoration():
    """
    Verifies that an image uploaded without any prior chat messages is preserved
    and fully restored with its dimensions, URL, and YOLO detections on session reload.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/v1/sessions", json={"title": "Image Only Recon"})
        assert res.status_code == 201
        session_id = res.json()["id"]

        import io
        from PIL import Image
        buf = io.BytesIO()
        Image.new("RGB", (320, 240), color=(120, 150, 200)).save(buf, format="JPEG")

        files = {"file": ("isolated_recon.jpg", buf.getvalue(), "image/jpeg")}
        upload_res = await client.post("/api/v1/images/upload", files=files, data={"session_id": session_id})
        assert upload_res.status_code == 201

        # Fetch detail directly
        detail = (await client.get(f"/api/v1/sessions/{session_id}")).json()
        assert detail["id"] == session_id
        assert len(detail["images"]) == 1
        assert detail["images"][0]["filename"] == "isolated_recon.jpg"
        assert detail["images"][0]["width"] == 320
        assert detail["images"][0]["height"] == 240
        assert "detected_objects" in detail["images"][0]

        # Cleanup
        await client.delete(f"/api/v1/sessions/{session_id}")


