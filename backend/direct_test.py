import pytest
from app.db.session import get_db
from sqlalchemy import text

@pytest.mark.asyncio
async def test_direct_db_connection():
    db_gen = get_db()
    session = await db_gen.__anext__()
    result = await session.execute(text("SELECT 1"))
    assert result.scalar() == 1