# backend/app/main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.deps import get_current_user
from app.api.routes.auth import router as auth_router
from app.api.routes.projects import router as projects_router
from app.api.routes.suites import router as suites_router
from app.api.routes.cases import router as cases_router
from app.api.routes.runs import router as runs_router
from app.api.routes.ingest import router as ingest_router

app = FastAPI(title=settings.PROJECT_NAME)

# (Optional) CORS while developing a separate frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

# Example protected endpoint
@app.get("/me")
async def me(user = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "role": user.role}

# Mount API v1 routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(projects_router, prefix=settings.API_V1_STR)
app.include_router(suites_router,   prefix=settings.API_V1_STR)
app.include_router(cases_router,    prefix=settings.API_V1_STR)
app.include_router(runs_router,     prefix=settings.API_V1_STR)
app.include_router(ingest_router,   prefix=settings.API_V1_STR)
