import pytest

pytestmark = pytest.mark.asyncio


async def test_register_login_me(client):
    resp = await client.post("/api/auth/register", json={"email": "a@example.com", "password": "longenough1"})
    assert resp.status_code == 201
    token = resp.json()["access_token"]

    resp = await client.post("/api/auth/login", json={"email": "a@example.com", "password": "longenough1"})
    assert resp.status_code == 200

    bad = await client.post("/api/auth/login", json={"email": "a@example.com", "password": "wrong-password"})
    assert bad.status_code == 401

    me = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "a@example.com"

    noauth = await client.get("/api/projects")
    assert noauth.status_code == 401


async def test_duplicate_register_rejected(client):
    await client.post("/api/auth/register", json={"email": "dup@example.com", "password": "longenough1"})
    dup = await client.post("/api/auth/register", json={"email": "dup@example.com", "password": "longenough1"})
    assert dup.status_code == 409


async def test_weak_password_rejected(client):
    resp = await client.post("/api/auth/register", json={"email": "w@example.com", "password": "short"})
    assert resp.status_code == 422
