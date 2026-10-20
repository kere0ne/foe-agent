import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..agent import runner
from ..auth import get_current_user
from ..db import get_db
from ..models import AgentRun, Project, User
from ..routers.chat_routes import provider_config
from ..routers.projects import owned_project
from ..schemas import RunIn
from ..services.files import project_root

router = APIRouter(prefix="/api/projects/{project_id}/runs", tags=["runs"])


@router.post("", status_code=202)
async def create_run(project_id: int, payload: RunIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await owned_project(project_id, user, db)
    cfg = await provider_config(payload.provider_id, user, db)
    run = AgentRun(project_id=project_id, user_id=user.id, goal=payload.goal, state="queued", steps=[])
    db.add(run)
    await db.commit()
    await db.refresh(run)
    root = project_root(project_id)
    task = asyncio.create_task(runner.execute_run(run.id, root, cfg, payload.goal, payload.verify_command))
    runner.RUNNING_TASKS[run.id] = task
    return {"id": run.id, "state": run.state}


@router.get("/{run_id}")
async def get_run(project_id: int, run_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await owned_project(project_id, user, db)
    row = (await db.execute(select(AgentRun).where(
        AgentRun.id == run_id, AgentRun.project_id == project_id, AgentRun.user_id == user.id))).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Run not found")
    return {"id": row.id, "goal": row.goal, "state": row.state, "steps": row.steps or [],
            "result": row.result, "error": row.error, "created_at": str(row.created_at)}


@router.post("/{run_id}/cancel")
async def cancel_run(project_id: int, run_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await owned_project(project_id, user, db)
    row = (await db.execute(select(AgentRun).where(
        AgentRun.id == run_id, AgentRun.project_id == project_id, AgentRun.user_id == user.id))).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Run not found")
    row.cancel_requested = True
    await db.commit()
    return {"id": row.id, "cancel_requested": True}


@router.get("")
async def list_runs(project_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await owned_project(project_id, user, db)
    rows = (await db.execute(select(AgentRun).where(
        AgentRun.project_id == project_id, AgentRun.user_id == user.id).order_by(AgentRun.id.desc()))).scalars().all()
    return [{"id": r.id, "goal": r.goal, "state": r.state, "result": r.result, "error": r.error} for r in rows]
