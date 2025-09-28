from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.db.schemas import RunOut
from app.db.crud import create_run, add_result
from app.db.models import ResultStatus

from junitparser import JUnitXml

router = APIRouter(prefix="/ingest", tags=["ingest"])

@router.post("/junit", response_model=RunOut, status_code=201)
async def ingest_junit(project_id: int,
                       file: UploadFile = File(...),
                       db: AsyncSession = Depends(get_db),
                       user=Depends(get_current_user)):
    # 1) create run
    run = await create_run(db, project_id=project_id, user_id=user.id, triggered_by_ci=True)

    # 2) parse junit
    content = await file.read()
    xml = JUnitXml.fromstring(content)

    # 3) each test case -> result
    # We will try to match cases by name. In a real app, map name -> case_id reliably.
    name_to_id = {}  # TODO: cache your cases or look them up by name

    for suite in xml:
        for case in suite:
            title = f"{suite.name or ''}::{case.name}"
            case_id = name_to_id.get(title)
            if not case_id:
                # For the MVP: skip unknown cases
                # OR create a placeholder case automatically if you prefer
                continue

            if case.result:  # has failure/skip
                # junitparser: case.result can be Failure, Skipped, etc.
                kind = case.result[0]._tag  # 'failure' or 'skipped'
                status = ResultStatus.fail if kind == "failure" else ResultStatus.skip
            else:
                status = ResultStatus.pass_

            duration_ms = int((case.time or 0) * 1000)
            await add_result(db, run.id, case_id, status.value, duration_ms, None)

    return run
