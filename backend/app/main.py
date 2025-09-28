from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.config import settings
from app.db.session import get_db
from app.api.routes.auth import router as auth_router
from app.api.deps import get_current_user
from app.api.routes.projects import router as projects_router
from app.api.routes.suites import router as suites_router
from app.api.routes.cases import router as cases_router
from app.api.routes.runs import router as runs_router
from app.api.routes.ingest import router as ingest_router




app = FastAPI(title=settings.PROJECT_NAME)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/health/db")
async def health_db(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))
    return {"db": "ok"}

# Example protected endpoint
@app.get("/me")
async def me(user = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "role": user.role}

# Mount API v1 routers
app.include_router(auth_router, prefix=settings.API_V1_STR)

app.include_router(projects_router, prefix=settings.API_V1_STR)

app.include_router(suites_router, prefix=settings.API_V1_STR)
app.include_router(cases_router, prefix=settings.API_V1_STR)
app.include_router(runs_router, prefix=settings.API_V1_STR)
app.include_router(ingest_router, prefix=settings.API_V1_STR)
