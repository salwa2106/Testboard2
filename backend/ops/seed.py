# backend/ops/seed.py
import asyncio, os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.db.models import (
    Base, User, UserRole, Project, Suite, Case,
    Run, Result, ResultStatus,
)
from app.core.security import hash_password


# Use backend/.env if present, or fallback to local default
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/testboard")

async def main() -> None:
    engine = create_async_engine(DATABASE_URL, future=True)
    async with engine.begin() as conn:
        # For dev/demo only; in prod prefer Alembic migrations
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as db:
        # --- Users ---
        admin = User(email="admin@test.com", password_hash=hash_password("admin123"), role=UserRole.admin)
        qa    = User(email="qa@test.com",    password_hash=hash_password("qa123"),    role=UserRole.qa)
        dev   = User(email="dev@test.com",   password_hash=hash_password("dev123"),   role=UserRole.dev)
        db.add_all([admin, qa, dev])
        await db.flush()  # get IDs

        # --- Project / Suite / Cases ---
        proj = Project(name="Demo Project", created_by=admin.id)
        suite = Suite(project_id=proj.id if getattr(proj, "id", None) else 0, name="Smoke")  # will set after flush
        db.add(proj)
        await db.flush()
        suite.project_id = proj.id
        db.add(suite)
        await db.flush()

        case_login = Case(suite_id=suite.id, title="Login works", steps="Open -> Fill -> Submit", expected="200 OK")
        case_create = Case(suite_id=suite.id, title="Create project", steps="POST /projects", expected="201 Created")
        db.add_all([case_login, case_create])
        await db.flush()

        # --- Run + Results ---
        run = Run(project_id=proj.id, created_by=qa.id, triggered_by_ci=False)
        db.add(run)
        await db.flush()

        r1 = Result(run_id=run.id, case_id=case_login.id, status=ResultStatus.pass_, duration_ms=850, evidence_url=None)
        r2 = Result(run_id=run.id, case_id=case_create.id, status=ResultStatus.fail, duration_ms=1200, evidence_url=None)
        db.add_all([r1, r2])

        await db.commit()

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
