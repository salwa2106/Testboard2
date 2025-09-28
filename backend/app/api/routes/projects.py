from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.db.schemas import ProjectCreate, ProjectOut
from app.db.crud import create_project, list_projects, get_project, delete_project

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("", response_model=ProjectOut, status_code=201)
async def create(payload: ProjectCreate,
                 db: AsyncSession = Depends(get_db),
                 user=Depends(get_current_user)):
    return await create_project(db, payload.name, user.id)

@router.get("", response_model=list[ProjectOut])
async def index(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return await list_projects(db)

@router.get("/{project_id}", response_model=ProjectOut)
async def show(project_id: int,
               db: AsyncSession = Depends(get_db),
               user=Depends(get_current_user)):
    proj = await get_project(db, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Not found")
    return proj

@router.delete("/{project_id}", status_code=204)
async def remove(project_id: int,
                 db: AsyncSession = Depends(get_db),
                 user=Depends(get_current_user)):
    await delete_project(db, project_id)
