import pytest

pytestmark = pytest.mark.asyncio


async def _project(auth_client):
    resp = await auth_client.post("/api/projects", json={"name": "demo", "description": ""})
    assert resp.status_code == 201
    return resp.json()["id"]


async def test_project_isolation(auth_client, client):
    pid = await _project(auth_client)
    await auth_client.put(f"/api/projects/{pid}/files", params={"path": "hello.txt"}, content="hi")
    other = await client.post("/api/auth/register", json={"email": "b@example.com", "password": "longenough1"})
    intruder = dict(client.headers)
    intruder["authorization"] = f"Bearer {other.json()['access_token']}"
    resp = await client.get(f"/api/projects/{pid}/files/tree", headers=intruder)
    assert resp.status_code == 404
    resp = await client.get(f"/api/projects/{pid}/files", params={"path": "hello.txt"}, headers=intruder)
    assert resp.status_code == 404


async def test_write_read_tree_delete(auth_client):
    pid = await _project(auth_client)
    resp = await auth_client.put(f"/api/projects/{pid}/files", params={"path": "src/main.py"}, content="print(1)")
    assert resp.status_code == 200
    resp = await auth_client.get(f"/api/projects/{pid}/files", params={"path": "src/main.py"})
    assert resp.json()["content"] == "print(1)"
    tree = (await auth_client.get(f"/api/projects/{pid}/files/tree")).json()
    names = [e["name"] for e in tree["tree"]]
    assert "src" in names
    resp = await auth_client.delete(f"/api/projects/{pid}/files", params={"path": "src/main.py"})
    assert resp.status_code == 200


async def test_path_traversal_blocked(auth_client):
    pid = await _project(auth_client)
    resp = await auth_client.get(f"/api/projects/{pid}/files", params={"path": "../etc/passwd"})
    assert resp.status_code == 400
    resp = await auth_client.put(f"/api/projects/{pid}/files", params={"path": "../../evil.txt"}, content="x")
    assert resp.status_code == 400
    resp = await auth_client.delete(f"/api/projects/{pid}/files", params={"path": "/etc"})
    assert resp.status_code == 400


async def test_zip_upload_safe_extraction(auth_client):
    import io
    import zipfile
    pid = await _project(auth_client)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("project/main.py", "print(2)")
        zf.writestr("../escape.py", "evil")
    buf.seek(0)
    resp = await auth_client.post(f"/api/projects/{pid}/files/upload",
                                  files={"file": ("proj.zip", buf.getvalue(), "application/zip")})
    assert resp.status_code == 400
    assert "escape" in resp.json()["detail"]
    ok = io.BytesIO()
    with zipfile.ZipFile(ok, "w") as zf:
        zf.writestr("main.py", "print(3)")
    ok.seek(0)
    resp = await auth_client.post(f"/api/projects/{pid}/files/upload",
                                  files={"file": ("proj.zip", ok.getvalue(), "application/zip")})
    assert resp.status_code == 200 and resp.json()["extracted"]["files"] == 1
