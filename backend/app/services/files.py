import os
import shutil
import zipfile
from pathlib import Path

from ..config import settings


class PathOutsideRoot(Exception):
    pass


SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".next", "dist"}


def project_root(project_id: int) -> Path:
    root = (Path(settings.data_dir) / "projects" / str(project_id)).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def safe_join(root: Path, rel: str) -> Path:
    if rel in ("", ".", "/"):
        return root
    candidate = (root / rel).resolve()
    if not candidate.is_relative_to(root):
        raise PathOutsideRoot(rel)
    return candidate


def tree(root: Path, max_entries: int = 2000, max_depth: int = 12) -> list[dict]:
    count = 0

    def walk(directory: Path, depth: int) -> list[dict]:
        nonlocal count
        entries = []
        try:
            children = sorted(directory.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except PermissionError:
            return []
        for child in children:
            if count >= max_entries or depth > max_depth:
                return entries
            if child.is_dir():
                if child.name in SKIP_DIRS:
                    continue
                count += 1
                entries.append({
                    "name": child.name,
                    "type": "dir",
                    "children": walk(child, depth + 1),
                })
            else:
                count += 1
                entries.append({"name": child.name, "type": "file", "size": child.stat().st_size})
        return entries

    return walk(root, 0)


def write_file(root: Path, rel: str, content: str) -> dict:
    target = safe_join(root, rel)
    if len(content.encode()) > settings.max_file_write_mb * 1024 * 1024:
        raise ValueError(f"File exceeds {settings.max_file_write_mb} MB write limit")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {"path": rel, "bytes": len(content.encode())}


def read_file(root: Path, rel: str, max_bytes: int = 2 * 1024 * 1024) -> str:
    target = safe_join(root, rel)
    if not target.is_file():
        raise FileNotFoundError(rel)
    if target.stat().st_size > max_bytes:
        raise ValueError("File too large to read through the API")
    return target.read_text(encoding="utf-8", errors="replace")


def delete_path(root: Path, rel: str) -> None:
    target = safe_join(root, rel)
    if target == root:
        raise ValueError("Refusing to delete the project root")
    if target.is_dir():
        shutil.rmtree(target)
    elif target.exists():
        target.unlink()
    else:
        raise FileNotFoundError(rel)


def extract_zip(root: Path, data: bytes, max_files: int = 2000, max_total_bytes: int = 100 * 1024 * 1024) -> dict:
    import io

    total = 0
    count = 0
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = archive.namelist()
        for name in names:
            candidate = (root / name).resolve()
            if not candidate.is_relative_to(root):
                raise ValueError(f"Unsafe path in archive: {name}")
        for info in archive.infolist():
            if info.is_dir():
                continue
            count += 1
            total += info.file_size
            if count > max_files or total > max_total_bytes:
                raise ValueError("Archive exceeds size or file-count limits")
        archive.extractall(root)
    return {"files": count, "bytes": total}
