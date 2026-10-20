import asyncio
import json
import re
from pathlib import Path

from ..db import SessionLocal
from ..llm.providers import ProviderConfig, ProviderError, stream_chat
from ..services import files as filesvc
from . import prompts, tools

RUNNING_TASKS: dict[int, asyncio.Task] = {}


def _extract_json(text: str) -> dict:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.+?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Model did not return a JSON object")
    return json.loads(text[start:end + 1])


async def _chat_json(cfg: ProviderConfig, messages: list[dict], run_steps: list) -> dict:
    parts = []
    async for chunk in stream_chat(cfg, messages):
        parts.append(chunk)
    text = "".join(parts)
    run_steps.append({"phase": "model", "preview": text[:500]})
    return _extract_json(text)


async def _set_state(run_id: int, **fields) -> None:
    from sqlalchemy import select, update
    from ..models import AgentRun
    async with SessionLocal() as db:
        await db.execute(update(AgentRun).where(AgentRun.id == run_id).values(**fields))
        await db.commit()


async def _append_steps(run_id: int, steps: list) -> None:
    from sqlalchemy import select
    from ..models import AgentRun
    async with SessionLocal() as db:
        row = (await db.execute(select(AgentRun).where(AgentRun.id == run_id))).scalar_one_or_none()
        if row is None:
            return
        merged = list(row.steps or []) + steps
        row.steps = merged  # type: ignore[assignment]
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(row, "steps")
        await db.commit()


class RunCancelled(Exception):
    pass


async def _check_cancel(run_id: int) -> None:
    from sqlalchemy import select
    from ..models import AgentRun
    async with SessionLocal() as db:
        row = (await db.execute(select(AgentRun.cancel_requested).where(AgentRun.id == run_id))).scalar_one_or_none()
    if row:
        raise RunCancelled()


async def execute_run(run_id: int, project_root: Path, cfg: ProviderConfig, goal: str, verify_command: str | None) -> None:
    steps: list = []
    try:
        await _set_state(run_id, state="planning")
        tree_text = "\n".join(
            f"{e['type'][0]} {e['name']}" for e in _flat_tree(project_root)
        ) or "(empty project)"
        plan = await _chat_json(cfg, [
            {"role": "system", "content": prompts.PLAN_SYSTEM},
            {"role": "user", "content": prompts.PLAN_USER.format(goal=goal, tree=tree_text)},
        ], steps)
        plan_steps = plan.get("steps") or []
        verify = verify_command or plan.get("verify") or None
        await _append_steps(run_id, [
            {"phase": "plan", "summary": plan.get("summary", ""), "n_steps": len(plan_steps),
             "steps": [{"purpose": s.get("purpose", ""), "action": s.get("action"), "path": s.get("path"), "command": s.get("command")} for s in plan_steps]},
            {"phase": "inspect", "tree": tree_text[:2000]},
        ])
        debug_rounds = 0
        failed: dict | None = None
        while True:
            for step in plan_steps:
                await _check_cancel(run_id)
                action = step.get("action")
                if action == "write_file":
                    result = tools.write_project_file(project_root, step.get("path", ""), step.get("content", ""))
                elif action == "run_command":
                    result = tools.run_command(project_root, step.get("command", ""))
                else:
                    result = {"ok": False, "error": f"Unknown action: {action}"}
                steps.append({"phase": "act", "purpose": step.get("purpose", ""), "action": action,
                              "detail": step.get("path") or step.get("command"), "result": result})
                if not result.get("ok"):
                    failed = {"step": {k: step.get(k) for k in ("purpose", "action", "path", "command")},
                              "result": {k: result.get(k) for k in ("error", "exit_code", "stdout", "stderr", "timed_out")}}
                    break
            else:
                failed = None

            await _append_steps(run_id, steps)
            steps = []

            if failed is None:
                if not verify:
                    await _set_state(run_id, state="complete", result=plan.get("summary", "Done"))
                    return
                await _check_cancel(run_id)
                vresult = tools.run_command(project_root, verify)
                await _append_steps(run_id, [{"phase": "verify", "command": verify, "result": vresult}])
                if vresult.get("ok"):
                    await _set_state(run_id, state="complete", result=plan.get("summary", "Verified"))
                    return
                failed = {"step": {"action": "run_command", "command": verify}, "result": vresult}

            debug_rounds += 1
            if debug_rounds > 3:
                await _set_state(run_id, state="failed", error="Verification kept failing after 3 debug rounds")
                return
            await _set_state(run_id, state=f"debugging (round {debug_rounds})")
            fix = await _chat_json(cfg, [
                {"role": "system", "content": prompts.DEBUG_SYSTEM},
                {"role": "user", "content": prompts.DEBUG_USER.format(
                    goal=goal, failed_step=json.dumps(failed["step"]),
                    exit_code=failed["result"].get("exit_code"),
                    output=(failed["result"].get("stdout", "") + failed["result"].get("stderr", ""))[:3000])},
            ], steps)
            plan_steps = fix.get("steps") or []
            if fix.get("verify"):
                verify = fix["verify"]
            failed = None
    except RunCancelled:
        await _append_steps(run_id, steps)
        await _set_state(run_id, state="cancelled")
    except ProviderError as exc:
        await _append_steps(run_id, steps)
        await _set_state(run_id, state="failed", error=f"Model error: {exc}")
    except Exception as exc:  # surface real failures instead of hanging a run
        await _append_steps(run_id, steps)
        await _set_state(run_id, state="failed", error=f"{exc.__class__.__name__}: {exc}")
    finally:
        RUNNING_TASKS.pop(run_id, None)


def _flat_tree(root: Path, limit: int = 120) -> list[dict]:
    flat: list[dict] = []

    def walk(directory: Path, prefix: str) -> None:
        if len(flat) >= limit:
            return
        try:
            children = sorted(directory.iterdir(), key=lambda p: (p.is_file(), p.name))
        except OSError:
            return
        for child in children:
            if child.name in filesvc.SKIP_DIRS or len(flat) >= limit:
                continue
            name = f"{prefix}{child.name}"
            flat.append({"type": "dir" if child.is_dir() else "file", "name": name})
            if child.is_dir():
                walk(child, name + "/")

    walk(root, "")
    return flat
