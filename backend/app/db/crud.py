from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import User, UserRole
from app.core.security import hash_password, verify_password
from app.db.models import Suite, Case
from sqlalchemy import select, func
from app.db.models import Run, Result, ResultStatus



async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    res = await db.execute(select(User).where(User.email == email))
    return res.scalar_one_or_none()

async def create_user(db: AsyncSession, email: str, password: str, role: UserRole) -> User:
    user = User(email=email, password_hash=hash_password(password), role=role)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def authenticate(db: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email)
    if user and verify_password(password, user.password_hash):
        return user
    return None

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Project

async def create_project(db: AsyncSession, name: str, user_id: int) -> Project:
    proj = Project(name=name, created_by=user_id)
    db.add(proj)
    await db.commit()
    await db.refresh(proj)
    return proj

async def list_projects(db: AsyncSession) -> list[Project]:
    res = await db.execute(select(Project).order_by(Project.id))
    return list(res.scalars().all())

async def get_project(db: AsyncSession, pid: int) -> Project | None:
    res = await db.execute(select(Project).where(Project.id == pid))
    return res.scalar_one_or_none()

async def delete_project(db: AsyncSession, pid: int) -> None:
    await db.execute(delete(Project).where(Project.id == pid))
    await db.commit()

# Suites
async def create_suite(db: AsyncSession, project_id: int, name: str) -> Suite:
    s = Suite(project_id=project_id, name=name)
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return s

async def list_suites(db: AsyncSession, project_id: int | None = None) -> list[Suite]:
    q = select(Suite).order_by(Suite.id)
    if project_id is not None:
        q = q.where(Suite.project_id == project_id)
    res = await db.execute(q)
    return list(res.scalars().all())

# Cases
async def create_case(db: AsyncSession, suite_id: int, title: str, steps: str | None, expected: str | None) -> Case:
    c = Case(suite_id=suite_id, title=title, steps=steps, expected=expected)
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return c

async def list_cases(db: AsyncSession, suite_id: int | None = None) -> list[Case]:
    q = select(Case).order_by(Case.id)
    if suite_id is not None:
        q = q.where(Case.suite_id == suite_id)
    res = await db.execute(q)
    return list(res.scalars().all())

async def create_run(db: AsyncSession, project_id: int, user_id: int, triggered_by_ci: bool) -> Run:
    r = Run(project_id=project_id, created_by=user_id, triggered_by_ci=triggered_by_ci)
    db.add(r)
    await db.commit()
    await db.refresh(r)
    return r

async def list_runs(db: AsyncSession, project_id: int | None = None) -> list[Run]:
    q = select(Run).order_by(Run.id.desc())
    if project_id is not None:
        q = q.where(Run.project_id == project_id)
    res = await db.execute(q)
    return list(res.scalars().all())

# Results
async def add_result(db: AsyncSession, run_id: int, case_id: int, status: str, duration_ms: int | None, evidence_url: str | None) -> Result:
    res = Result(run_id=run_id, case_id=case_id, status=ResultStatus(status), duration_ms=duration_ms, evidence_url=evidence_url)
    db.add(res)
    await db.commit()
    await db.refresh(res)
    return res

async def list_results(db: AsyncSession, run_id: int) -> list[Result]:
    q = select(Result).where(Result.run_id == run_id).order_by(Result.id)
    res = await db.execute(q)
    return list(res.scalars().all())

async def run_summary(db: AsyncSession, run_id: int) -> dict:
    q = select(
        func.count(Result.id),
        func.sum(func.case((Result.status == ResultStatus.pass_, 1), else_=0)),
        func.sum(func.case((Result.status == ResultStatus.fail, 1), else_=0)),
        func.sum(func.case((Result.status == ResultStatus.skip, 1), else_=0)),
    ).where(Result.run_id == run_id)
    total, passed, failed, skipped = (await db.execute(q)).one()
    return {"run_id": run_id, "total": total or 0, "passed": passed or 0, "failed": failed or 0, "skipped": skipped or 0}