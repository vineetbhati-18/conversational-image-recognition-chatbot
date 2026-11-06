import pytest
from httpx import AsyncClient, ASGITransport
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import create_app


@pytest.mark.asyncio
async def test_app_factory_instance():
    test_app = create_app()
    assert test_app.title == "BEL Conversational Image Recognition Backend"
    assert test_app.version == "1.0.0"

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test Root
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"

        # Test CORS headers on preflight
        cors_response = await client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert cors_response.status_code == 200
        assert "access-control-allow-origin" in cors_response.headers
