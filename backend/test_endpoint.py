import pytest
import httpx


@pytest.mark.asyncio
async def test_health_endpoints():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://127.0.0.1:8001/health")
        assert response.status_code == 200

        response = await client.get("http://127.0.0.1:8001/health/db")
        assert response.status_code == 200