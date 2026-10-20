import os
import subprocess
from pathlib import Path

from ..config import settings
from ..services.files import PathOutsideRoot, safe_join


def run_command(root: Path, command: str, timeout: int | None = None) -> dict:
    timeout = timeout or settings.command_timeout
    env = {
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
        "HOME": str(root),
        "LANG": "C.UTF-8",
        "PYTHONUNBUFFERED": "1",
        "NO_COLOR": "1",
    }
    try:
        proc = subprocess.run(
            ["bash", "-lc", command],
            cwd=str(root),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "ok": proc.returncode == 0,
            "exit_code": proc.returncode,
            "stdout": proc.stdout[-8000:],
            "stderr": proc.stderr[-8000:],
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "exit_code": None,
            "stdout": (exc.stdout or "")[-8000:] if isinstance(exc.stdout, str) else "",
            "stderr": (exc.stderr or "")[-8000:] if isinstance(exc.stderr, str) else "",
            "timed_out": True,
        }


def write_project_file(root: Path, rel: str, content: str) -> dict:
    try:
        target = safe_join(root, rel)
    except PathOutsideRoot:
        return {"ok": False, "error": f"Blocked path outside project root: {rel}"}
    target.parent.mkdir(parents=True, exist_ok=True)
    if len(content.encode()) > settings.max_file_write_mb * 1024 * 1024:
        return {"ok": False, "error": f"File exceeds {settings.max_file_write_mb} MB write limit"}
    target.write_text(content, encoding="utf-8")
    return {"ok": True, "path": rel, "bytes": len(content.encode())}
