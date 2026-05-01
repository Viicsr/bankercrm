import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import app

SQLALCHEMY_TEST_URL = "sqlite+aiosqlite:///./test.db"
engine_test = create_async_engine(SQLALCHEMY_TEST_URL)
TestingSessionLocal = async_sessionmaker(engine_test, expire_on_commit=False)


async def _create_tables():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _drop_tables():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function", autouse=True)
def setup_db():
    asyncio.run(_create_tables())
    yield
    asyncio.run(_drop_tables())


@pytest.fixture
def client():
    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def admin_headers(client) -> dict:
    client.post(
        "/api/v1/auth/register",
        json={"email": "testadmin@test.com", "password": "Admin1234!", "role": "admin"},
    )
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "testadmin@test.com", "password": "Admin1234!"},
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def readonly_user(client):
    """Crea un usuario con rol read_only para tests de permisos."""
    client.post(
        "/api/v1/auth/register",
        json={"email": "readonly_403@test.com", "password": "Read1234!", "role": "read_only"},
    )
    return {"email": "readonly_403@test.com", "password": "Read1234!"}


@pytest.fixture
def admin_user(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "admin@test.com", "password": "Admin1234!", "role": "admin"},
    )
    return {"email": "admin@test.com", "password": "Admin1234!"}


@pytest.fixture
def analyst_user(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "analyst@test.com", "password": "Analyst1234!", "role": "analyst"},
    )
    return {"email": "analyst@test.com", "password": "Analyst1234!"}
