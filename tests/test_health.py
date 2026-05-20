from unittest.mock import AsyncMock, MagicMock, patch


async def test_health_check_ok(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "dependencies" in data
    assert "database" in data["dependencies"]
    assert data["dependencies"]["database"]["status"] == "ok"
    assert isinstance(data["dependencies"]["database"]["latency_ms"], float)
    assert "version" in data
    assert "environment" in data


async def test_health_check_db_unreachable(client):
    # Simula que engine.begin() lanza una excepción genérica
    with patch("app.main.engine") as mock_engine:
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(side_effect=Exception("DB unreachable"))
        mock_cm.__aexit__ = AsyncMock(return_value=False)
        mock_engine.begin.return_value = mock_cm

        response = await client.get("/health")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "degraded"
    assert data["dependencies"]["database"]["status"] == "degraded"
    assert data["dependencies"]["database"]["latency_ms"] is None


async def test_health_check_db_timeout(client):
    # Simula que la BD responde, pero tarda más de 5 segundos
    import asyncio

    async def slow_execute(*args, **kwargs):
        await asyncio.sleep(10)  # más que el timeout de 5s

    with patch("app.main.engine") as mock_engine:
        mock_conn = AsyncMock()
        mock_conn.execute = slow_execute
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_cm.__aexit__ = AsyncMock(return_value=False)
        mock_engine.begin.return_value = mock_cm

        response = await client.get("/health")

    assert response.status_code == 503
    data = response.json()
    assert data["dependencies"]["database"]["status"] == "unavailable"
