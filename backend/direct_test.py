import asyncio
from app.db.session import get_db
from sqlalchemy import text

async def test():
    try:
        db_gen = get_db()
        session = await db_gen.__anext__()
        result = await session.execute(text("SELECT 1"))
        print(f"Direct DB test: SUCCESS - {result.scalar()}")
    except Exception as e:
        print(f"Direct DB test FAILED: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test())