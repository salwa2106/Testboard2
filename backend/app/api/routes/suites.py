from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.db.schemas import SuiteCreate, SuiteOut
from app.db.crud import create_suite, list_suites

router = APIRouter(prefix="/suites", tags=["suites"])

@router.post("", response_model=SuiteOut, status_code=201)
async def create(payload: SuiteCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return await create_suite(db, payload.project_id, payload.name)

@router.get("", response_model=list[SuiteOut])
async def index(project_id: int | None = None, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return await list_suites(db, project_id)
