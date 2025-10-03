# backend/test_endpoint.py
import pytest
import httpx
from httpx import ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_health_endpoints():
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"} or resp.text.lower().startswith("ok")
