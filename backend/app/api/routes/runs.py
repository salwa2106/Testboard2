from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.db.schemas import RunCreate, RunOut, ResultCreate, ResultOut, RunSummary
from app.db.crud import create_run, list_runs, add_result, list_results, run_summary
from typing import List
from fastapi import Body

router = APIRouter(prefix="/runs", tags=["runs"])

@router.post("", response_model=RunOut, status_code=201)
async def create(payload: RunCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return await create_run(db, payload.project_id, user.id, payload.triggered_by_ci)

@router.get("", response_model=list[RunOut])
async def index(project_id: int | None = None, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return await list_runs(db, project_id)

@router.post("/{run_id}/results", response_model=ResultOut, status_code=201)
async def add_one(run_id: int, payload: ResultCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return await add_result(db, run_id, payload.case_id, payload.status.value, payload.duration_ms, payload.evidence_url)

@router.get("/{run_id}/results", response_model=list[ResultOut])
async def list_for_run(run_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return await list_results(db, run_id)

@router.get("/{run_id}/summary", response_model=RunSummary)
async def summary(run_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    data = await run_summary(db, run_id)
    return data

@router.post("/{run_id}/results/bulk", response_model=list[ResultOut], status_code=201)
async def add_bulk(run_id: int,
                   payload: List[ResultCreate] = Body(...),
                   db: AsyncSession = Depends(get_db),
                   user=Depends(get_current_user)):
    created = []
    for item in payload:
        created.append(
            await add_result(db, run_id, item.case_id, item.status.value, item.duration_ms, item.evidence_url)
        )
    return created