from unittest.mock import AsyncMock
from app.core.database import get_db
from app.main import app


async def test_health_check_ok(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["db"] == "connected"
    assert "version" in data
    assert "environment" in data


async def test_health_check_db_unreachable(client):
    async def broken_get_db():
        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("DB unreachable")
        yield mock_session

    app.dependency_overrides[get_db] = broken_get_db
    try:
        response = await client.get("/health")
        assert response.status_code == 503
        assert response.json()["db"] == "unreachable"
    finally:
        app.dependency_overrides.pop(get_db, None)
