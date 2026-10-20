import asyncio
import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

os.environ["FOE_JWT_SECRET"] = "test-secret"
os.environ["FOE_DATA_DIR"] = os.environ.get("FOE_TEST_DATA_DIR", "/tmp/foe-test-data")

from app.db import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_engine(tmp_path, monkeypatch):
    import app.config as config
    import app.db as dbmod

    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/test.db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(dbmod, "SessionLocal", session_factory)
    import app.agent.runner as runner
    monkeypatch.setattr(runner, "SessionLocal", session_factory)
    monkeypatch.setattr(config.settings, "data_dir", str(tmp_path / "data"))
    yield engine
    await engine.dispose()
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(db_engine):
    from app.routers.auth_routes import limiter
    limiter._hits.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def auth_client(client):
    resp = await client.post("/api/auth/register", json={"email": "dev@example.com", "password": "hunter2boogaloo"})
    token = resp.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client
