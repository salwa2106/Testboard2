from __future__ import annotations

# --- Make "app" importable when Alembic runs from the repo root ---
import os, sys

# env.py is inside backend/alembic/, so go up one level to backend/
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


# --- Standard Alembic imports/config ---
from logging.config import fileConfig
from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

# Load app settings & metadata
from dotenv import load_dotenv
from app.core.config import settings
from app.db.base import Base

# Load variables from backend/.env that Jenkins writes
load_dotenv(os.path.join(BACKEND_DIR, ".env"))

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# If you have models' metadata, keep this:
target_metadata = Base.metadata  # or set to None if you don't use autogenerate

def _get_db_url() -> str:
    """Prefer env var (from .env), fallback to app settings."""
    return os.getenv("DATABASE_URL") or settings.DATABASE_URL

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = _get_db_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def _run_sync_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    """Run migrations in 'online' mode' using async engine."""
    url = _get_db_url()
    engine = create_async_engine(url, poolclass=pool.NullPool, future=True)
    async with engine.connect() as connection:
        await connection.run_sync(_run_sync_migrations)
    await engine.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    import asyncio
    asyncio.run(run_migrations_online())
