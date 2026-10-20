from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse

from ..auth import get_current_user
from ..config import settings
from ..db import get_db
from ..models import User
from ..services import files as filesvc
from .projects import owned_project

router = APIRouter(prefix="/api/projects/{project_id}/files", tags=["files"])


@router.get("/tree")
async def tree(project_id: int, user: User = Depends(get_current_user), db=Depends(get_db)):
    await owned_project(project_id, user, db)
    return {"tree": filesvc.tree(filesvc.project_root(project_id))}


@router.get("")
async def read(project_id: int, path: str, user: User = Depends(get_current_user), db=Depends(get_db)):
    await owned_project(project_id, user, db)
    root = filesvc.project_root(project_id)
    try:
        content = filesvc.read_file(root, path)
    except FileNotFoundError:
        raise HTTPException(404, "File not found")
    except filesvc.PathOutsideRoot:
        raise HTTPException(400, "Path escapes the project root")
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return {"path": path, "content": content}


@router.put("")
async def write(project_id: int, path: str, request: Request, user: User = Depends(get_current_user), db=Depends(get_db)):
    await owned_project(project_id, user, db)
    content = (await request.body()).decode("utf-8")
    root = filesvc.project_root(project_id)
    try:
        result = filesvc.write_file(root, path, content)
    except filesvc.PathOutsideRoot:
        raise HTTPException(400, "Path escapes the project root")
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return result


@router.post("/upload")
async def upload(project_id: int, file: UploadFile, user: User = Depends(get_current_user), db=Depends(get_db)):
    await owned_project(project_id, user, db)
    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"Upload exceeds {settings.max_upload_mb} MB limit")
    root = filesvc.project_root(project_id)
    name = file.filename or "upload.bin"
    if name.lower().endswith(".zip"):
        try:
            result = filesvc.extract_zip(root, data)
        except ValueError as exc:
            raise HTTPException(400, str(exc))
        return {"extracted": result}
    try:
        target = filesvc.safe_join(root, name)
    except filesvc.PathOutsideRoot:
        raise HTTPException(400, "Unsafe filename")
    target.write_bytes(data)
    return {"saved": name, "bytes": len(data)}


@router.delete("")
async def delete(project_id: int, path: str, user: User = Depends(get_current_user), db=Depends(get_db)):
    await owned_project(project_id, user, db)
    try:
        filesvc.delete_path(filesvc.project_root(project_id), path)
    except FileNotFoundError:
        raise HTTPException(404, "Not found")
    except filesvc.PathOutsideRoot:
        raise HTTPException(400, "Path escapes the project root")
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return {"deleted": path}


@router.get("/download")
async def download(project_id: int, path: str, user: User = Depends(get_current_user), db=Depends(get_db)):
    await owned_project(project_id, user, db)
    root = filesvc.project_root(project_id)
    try:
        target = filesvc.safe_join(root, path)
    except filesvc.PathOutsideRoot:
        raise HTTPException(400, "Path escapes the project root")
    if not target.is_file():
        raise HTTPException(404, "File not found")
    return FileResponse(target, filename=target.name)
