from unittest.mock import AsyncMock, patch

import pytest

from app.schemas.ai_insights import ClientInsight
from app.services.ai_insight_service import AIInsightService, AIServiceError
from tests.test_auth import get_auth_headers

MOCK_INSIGHT = ClientInsight(
    summary="Active client with a savings account of 1,000 EUR.",
    risk_profile="low",
    key_observation="A single active savings account with a moderate balance.",
    recommended_action="Review product fit on the next scheduled contact.",
)


async def _create_client_with_account(client, headers) -> int:
    client_res = await client.post(
        "/api/v1/clients/",
        json={"name": "AI Test Client", "email": "ai-insight@bank.es"},
        headers=headers,
    )
    assert client_res.status_code == 201
    client_id = client_res.json()["id"]

    account_res = await client.post(
        "/api/v1/accounts/",
        params={"client_id": client_id},
        json={
            "account_number": "AI001",
            "account_type": "savings",
            "balance": "1000.00",
        },
        headers=headers,
    )
    assert account_res.status_code == 201
    return client_id


async def test_get_client_insight(client, admin_headers):
    client_id = await _create_client_with_account(client, admin_headers)

    with patch(
        "app.services.ai_insight_service.AIInsightService._generate_insight",
        new_callable=AsyncMock,
        return_value=MOCK_INSIGHT,
    ) as mock_generate:
        response = await client.post(
            f"/api/v1/ai/clients/{client_id}/insights",
            json={"question": "What risk profile does this client have?"},
            headers=admin_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["client_id"] == client_id
    assert data["question"] == "What risk profile does this client have?"
    assert data["insight"]["risk_profile"] == "low"
    assert data["insight"]["summary"] == MOCK_INSIGHT.summary
    payload = mock_generate.await_args.args[0]
    assert payload["client_name"] == "AI Test Client"
    assert "savings" in payload["accounts_summary"]
    assert "1000" in payload["accounts_summary"]


async def test_get_client_insight_without_accounts(client, admin_headers):
    client_res = await client.post(
        "/api/v1/clients/",
        json={"name": "No Accounts", "email": "no-accounts@bank.es"},
        headers=admin_headers,
    )
    client_id = client_res.json()["id"]

    with patch(
        "app.services.ai_insight_service.AIInsightService._generate_insight",
        new_callable=AsyncMock,
        return_value=MOCK_INSIGHT,
    ) as mock_generate:
        response = await client.post(
            f"/api/v1/ai/clients/{client_id}/insights",
            json={"question": "What is the risk?"},
            headers=admin_headers,
        )

    assert response.status_code == 200
    assert mock_generate.await_args.args[0]["accounts_summary"] == "Sin cuentas registradas."


async def test_get_client_insight_not_found(client, admin_headers):
    with patch(
        "app.services.ai_insight_service.AIInsightService._generate_insight",
        new_callable=AsyncMock,
        return_value=MOCK_INSIGHT,
    ):
        response = await client.post(
            "/api/v1/ai/clients/99999/insights",
            json={"question": "What is the risk?"},
            headers=admin_headers,
        )

    assert response.status_code == 404
    assert response.json()["error"] == "NotFoundError"


async def test_get_client_insight_requires_auth(client):
    response = await client.post(
        "/api/v1/ai/clients/1/insights",
        json={"question": "What is the risk?"},
    )
    assert response.status_code == 401


async def test_get_client_insight_forbidden_for_readonly(client, readonly_user, admin_headers):
    client_id = await _create_client_with_account(client, admin_headers)
    headers = await get_auth_headers(client, readonly_user["email"], readonly_user["password"])
    response = await client.post(
        f"/api/v1/ai/clients/{client_id}/insights",
        json={"question": "What is the risk?"},
        headers=headers,
    )
    assert response.status_code == 403


async def test_get_client_insight_validation_error(client, admin_headers):
    response = await client.post(
        "/api/v1/ai/clients/1/insights",
        json={"question": ""},
        headers=admin_headers,
    )
    assert response.status_code == 422
    assert response.json()["error"] == "ValidationError"


async def test_get_client_insight_provider_failure(client, admin_headers):
    client_id = await _create_client_with_account(client, admin_headers)

    with patch(
        "app.services.ai_insight_service.AIInsightService._generate_insight",
        new_callable=AsyncMock,
        side_effect=AIServiceError("AI provider unavailable"),
    ):
        response = await client.post(
            f"/api/v1/ai/clients/{client_id}/insights",
            json={"question": "What is the risk?"},
            headers=admin_headers,
        )

    assert response.status_code == 502
    assert response.json()["error"] == "AIServiceError"


async def test_generate_insight_requires_api_key(db_session):
    service = AIInsightService(db_session)
    with patch("app.services.ai_insight_service.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = None
        with pytest.raises(AIServiceError, match="OPENAI_API_KEY"):
            await service._generate_insight({"question": "What is the risk?"})


async def test_generate_insight_wraps_provider_errors(db_session):
    service = AIInsightService(db_session)
    with patch("app.services.ai_insight_service.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = "sk-test"
        mock_settings.OPENAI_MODEL = "gpt-4o-mini"
        with patch(
            "app.services.ai_insight_service.ChatOpenAI",
            side_effect=RuntimeError("provider down"),
        ):
            with pytest.raises(AIServiceError, match="unavailable"):
                await service._generate_insight({"question": "What is the risk?"})
