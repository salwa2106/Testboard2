import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test():
    try:
        engine = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost:5432/testboard")
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("Database connection works!", result.scalar())
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test())