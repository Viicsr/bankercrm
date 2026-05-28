from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

# Respuesta simulada del BCE
MOCK_ECB_RATES = {
    "USD": {"rate": Decimal("1.0823"), "date": "2026-04-16", "base": "EUR"},
    "GBP": {"rate": Decimal("0.8521"), "date": "2026-04-16", "base": "EUR"},
    "JPY": {"rate": Decimal("163.45"), "date": "2026-04-16", "base": "EUR"},
}


@pytest.mark.anyio
async def test_get_fx_rates(client, admin_headers):
    with patch(
        "app.api.v1.routers.fx.fetch_fx_rates",
        new_callable=AsyncMock,
        return_value=MOCK_ECB_RATES,
    ):
        response = await client.get("/api/v1/fx/rates", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "rates" in data
    assert data["source"] == "European Central Bank"
    assert len(data["rates"]) == 3
    currencies = [r["currency"] for r in data["rates"]]
    assert currencies == sorted(currencies)


@pytest.mark.anyio
async def test_get_fx_rates_with_currency_filter(client, admin_headers):
    mock = AsyncMock(return_value=MOCK_ECB_RATES)
    with patch("app.api.v1.routers.fx.fetch_fx_rates", mock):
        response = await client.get(
            "/api/v1/fx/rates?currencies=USD&currencies=GBP",
            headers=admin_headers,
        )
    assert response.status_code == 200
    mock.assert_called_once_with(["USD", "GBP"])


@pytest.mark.anyio
async def test_get_fx_rates_requires_auth(client):
    response = await client.get("/api/v1/fx/rates")
    assert response.status_code == 401


@pytest.mark.anyio
async def test_convert_account_balance(client, admin_headers):
    client_res = await client.post(
        "/api/v1/clients/",  # trailing slash
        json={"name": "FX Test Client", "email": "fxtest@bank.es"},
        headers=admin_headers,
    )
    client_id = client_res.json()["id"]

    account_res = await client.post(
        "/api/v1/accounts/",
        params={"client_id": client_id},
        json={
            "account_number": "FX001",
            "account_type": "savings",
            "balance": "1000.00",
        },
        headers=admin_headers,
    )
    account_id = account_res.json()["id"]

    with patch(
        "app.api.v1.routers.fx.fetch_fx_rates",
        new_callable=AsyncMock,
        return_value=MOCK_ECB_RATES,
    ):
        response = await client.get(
            f"/api/v1/fx/accounts/{account_id}/convert?currencies=USD&currencies=GBP",
            headers=admin_headers,
        )
    assert response.status_code == 200
    data = response.json()
    assert data["balance_eur"] == 1000.0
    assert "USD" in data["conversions"]
    assert "GBP" in data["conversions"]
    assert abs(data["conversions"]["USD"]["amount"] - 1082.30) < 0.01


@pytest.mark.anyio
async def test_convert_nonexistent_account(client, admin_headers):
    with patch(
        "app.api.v1.routers.fx.fetch_fx_rates",
        new_callable=AsyncMock,
        return_value=MOCK_ECB_RATES,
    ):
        response = await client.get(
            "/api/v1/fx/accounts/99999/convert",
            headers=admin_headers,
        )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_ecb_api_failure_returns_502(client, admin_headers):
    from app.services.ecb_service import ECBServiceError

    with patch(
        "app.api.v1.routers.fx.fetch_fx_rates",
        new_callable=AsyncMock,
        side_effect=ECBServiceError("ECB API timeout"),
    ):
        response = await client.get("/api/v1/fx/rates", headers=admin_headers)
    assert response.status_code == 502
    assert "ECB" in response.json()["detail"]
