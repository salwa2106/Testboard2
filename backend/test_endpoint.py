import asyncio
import httpx


async def test():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://127.0.0.1:8000/health")
            print(f"Health endpoint: {response.status_code} - {response.text}")

            response = await client.get("http://127.0.0.1:8000/health/db")
            print(f"DB Health endpoint: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


asyncio.run(test())