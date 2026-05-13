import os

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import app
import logging

logging.getLogger("aiosqlite").setLevel(logging.WARNING)
TEST_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")


@pytest_asyncio.fixture(scope="function")
async def engine():
    """Crea el engine DENTRO del loop de pytest-asyncio, no a nivel de módulo."""
    _engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield _engine
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(engine):
    TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        follow_redirects=True,
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_headers(client) -> dict:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "testadmin@test.com", "password": "Admin1234!", "role": "admin"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        data={"username": "testadmin@test.com", "password": "Admin1234!"},
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def readonly_user(client) -> dict:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "readonly_403@test.com", "password": "Read1234!", "role": "read_only"},
    )
    return {"email": "readonly_403@test.com", "password": "Read1234!"}


@pytest_asyncio.fixture
async def admin_user(client) -> dict:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "admin@test.com", "password": "Admin1234!", "role": "admin"},
    )
    return {"email": "admin@test.com", "password": "Admin1234!"}


@pytest_asyncio.fixture
async def analyst_user(client) -> dict:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "analyst@test.com", "password": "Analyst1234!", "role": "analyst"},
    )
    return {"email": "analyst@test.com", "password": "Analyst1234!"}
