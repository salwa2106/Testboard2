import pytest
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

@pytest.mark.asyncio
async def test_database_connection():
    engine = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost:5432/testboard")
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar() == 1