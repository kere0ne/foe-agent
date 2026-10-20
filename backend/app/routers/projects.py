from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user
from ..db import get_db
from ..models import Project, User
from ..schemas import ProjectIn, ProjectOut

router = APIRouter(prefix="/api/projects", tags=["projects"])


async def owned_project(project_id: int, user: User, db: AsyncSession) -> Project:
    project = (await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )).scalar_one_or_none()
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    return project


@router.get("", response_model=list[ProjectOut])
async def list_projects(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Project).where(Project.user_id == user.id).order_by(Project.updated_at.desc()))).scalars().all()
    return rows


@router.post("", response_model=ProjectOut, status_code=201)
async def create_project(payload: ProjectIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    project = Project(user_id=user.id, name=payload.name, description=payload.description)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    from ..services.files import project_root
    project_root(project.id)
    return project


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await owned_project(project_id, user, db)


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    import shutil
    from ..services.files import project_root
    project = await owned_project(project_id, user, db)
    await db.delete(project)
    await db.commit()
    shutil.rmtree(project_root(project_id), ignore_errors=True)
