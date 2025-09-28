from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.db.schemas import CaseCreate, CaseOut
from app.db.crud import create_case, list_cases

router = APIRouter(prefix="/cases", tags=["cases"])

@router.post("", response_model=CaseOut, status_code=201)
async def create(payload: CaseCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return await create_case(db, payload.suite_id, payload.title, payload.steps, payload.expected)

@router.get("", response_model=list[CaseOut])
async def index(suite_id: int | None = None, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return await list_cases(db, suite_id)
