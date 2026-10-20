import json

import pytest
import pytest_asyncio

from app.agent import runner
from app.llm.providers import ProviderConfig

pytestmark = pytest.mark.asyncio


class FakeProvider:
    """Scripted stand-in for a model server: returns queued replies in order."""

    def __init__(self, replies):
        self.replies = list(replies)

    async def stream_chat(self, cfg, messages):
        if not self.replies:
            raise AssertionError("FakeProvider ran out of scripted replies")
        yield self.replies.pop(0)


async def _make_run(auth_client, *_ignored):
    resp = await auth_client.post("/api/projects", json={"name": "agentbox", "description": ""})
    pid = resp.json()["id"]
    resp = await auth_client.post("/api/models", json={
        "name": "fake", "kind": "openai_compat", "base_url": "http://fake.local",
        "model": "fake-model", "api_key": "", "is_default": True})
    return pid, resp.json()["id"]


async def test_full_run_completes_and_verifies(auth_client, db_engine, monkeypatch, tmp_path):
    import app.db as dbmod
    pid, _ = await _make_run(auth_client)
    fake = FakeProvider([
        json.dumps({"summary": "create hello script", "steps": [
            {"purpose": "write the script", "action": "write_file", "path": "hello.py", "content": "print('hello from foe')"},
            {"purpose": "run it", "action": "run_command", "command": "python3 hello.py"},
        ], "verify": "python3 hello.py"}),
    ])
    monkeypatch.setattr(runner, "stream_chat", fake.stream_chat)
    run_resp = await auth_client.post(f"/api/projects/{pid}/runs",
                                      json={"goal": "make hello.py", "provider_id": 1})
    assert run_resp.status_code == 202
    run_id = run_resp.json()["id"]
    task = runner.RUNNING_TASKS[run_id]
    await task
    detail = (await auth_client.get(f"/api/projects/{pid}/runs/{run_id}")).json()
    assert detail["state"] == "complete", detail
    assert "hello" in detail["result"]
    phases = [s["phase"] for s in detail["steps"]]
    assert "plan" in phases and "inspect" in phases and "verify" in phases
    from pathlib import Path
    from app.config import settings
    assert (Path(settings.data_dir) / "projects" / str(pid) / "hello.py").exists()


async def test_run_recovers_from_failure_via_debug(auth_client, db_engine, monkeypatch):
    pid, _ = await _make_run(auth_client)
    fake = FakeProvider([
        json.dumps({"summary": "script with a typo", "steps": [
            {"purpose": "write broken", "action": "write_file", "path": "broken.py", "content": "print('x'"},
            {"purpose": "run", "action": "run_command", "command": "python3 broken.py"},
        ], "verify": "python3 broken.py"}),
        json.dumps({"summary": "fixed the syntax", "steps": [
            {"purpose": "write fixed", "action": "write_file", "path": "broken.py", "content": "print('fixed')"},
        ], "verify": "python3 broken.py"}),
    ])
    monkeypatch.setattr(runner, "stream_chat", fake.stream_chat)
    run_resp = await auth_client.post(f"/api/projects/{pid}/runs",
                                      json={"goal": "fix and run", "provider_id": 1})
    run_id = run_resp.json()["id"]
    await runner.RUNNING_TASKS[run_id]
    detail = (await auth_client.get(f"/api/projects/{pid}/runs/{run_id}")).json()
    assert detail["state"] == "complete", detail
    phases = [s["phase"] for s in detail["steps"]]
    assert "verify" in phases and phases.count("act") >= 2


async def test_run_cancelled_between_steps(auth_client, db_engine, monkeypatch):
    from app.models import AgentRun
    import sqlalchemy as sa
    pid, _ = await _make_run(auth_client)
    fake = FakeProvider([
        json.dumps({"summary": "long plan", "steps": [
            {"purpose": "one", "action": "run_command", "command": "sleep 0.1"},
            {"purpose": "two", "action": "run_command", "command": "sleep 0.1"},
            {"purpose": "three", "action": "run_command", "command": "sleep 0.1"},
        ], "verify": "true"}),
    ])
    monkeypatch.setattr(runner, "stream_chat", fake.stream_chat)
    run_resp = await auth_client.post(f"/api/projects/{pid}/runs",
                                      json={"goal": "cancel me", "provider_id": 1})
    run_id = run_resp.json()["id"]
    task = runner.RUNNING_TASKS[run_id]
    await auth_client.post(f"/api/projects/{pid}/runs/{run_id}/cancel")
    await task
    detail = (await auth_client.get(f"/api/projects/{pid}/runs/{run_id}")).json()
    assert detail["state"] == "cancelled", detail


async def test_model_connection_test_reports_real_result(auth_client, monkeypatch):
    import httpx
    from app.llm import providers as prov

    async def fake_get(self, url, **kwargs):
        request = httpx.Request("GET", url)
        return httpx.Response(200, request=request, json={"models": [{"name": "llama3.2:1b"}]})

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    resp = await auth_client.post("/api/models", json={
        "name": "ollama", "kind": "ollama", "base_url": "http://localhost:11434",
        "model": "llama3.2:1b", "api_key": "", "is_default": False})
    pid = resp.json()["id"]
    result = (await auth_client.post(f"/api/models/{pid}/test")).json()
    assert result["ok"] is True and "llama3.2:1b" in result["models"]
