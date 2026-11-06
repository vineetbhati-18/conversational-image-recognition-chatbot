import pytest
from httpx import AsyncClient, ASGITransport
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import app


@pytest.mark.asyncio
async def test_request_logging_headers():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert "x-request-id" in response.headers
        assert "x-response-time" in response.headers
        assert response.headers["x-response-time"].endswith("ms")


@pytest.mark.asyncio
async def test_custom_request_id_passthrough():
    transport = ASGITransport(app=app)
    custom_id = "recon-audit-99"
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/", headers={"X-Request-ID": custom_id})
        assert response.status_code == 200
        assert response.headers["x-request-id"] == custom_id
