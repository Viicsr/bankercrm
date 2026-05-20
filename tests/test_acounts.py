from decimal import Decimal

import pytest_asyncio


@pytest_asyncio.fixture
async def existing_client(client, admin_headers):
    response = await client.post(
        "/api/v1/clients",
        json={"name": "Test Client", "email": "accounts@test.com"},
        headers=admin_headers,
    )
    assert response.status_code == 201
    return response.json()


async def test_create_account(client, existing_client, admin_headers):
    response = await client.post(
        "/api/v1/accounts",
        params={"client_id": existing_client["id"]},
        json={"account_number": "ES001", "account_type": "checking", "balance": "1000.00"},
        headers=admin_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["account_number"] == "ES001"
    assert data["client_id"] == existing_client["id"]
    assert Decimal(data["balance"]) == Decimal("1000.00")


async def test_create_account_negative_balance(client, existing_client, admin_headers):
    response = await client.post(
        "/api/v1/accounts",
        params={"client_id": existing_client["id"]},
        json={"account_number": "ES002", "account_type": "savings", "balance": "-50.00"},
        headers=admin_headers,
    )
    assert response.status_code == 422


async def test_create_account_duplicate_number(client, existing_client, admin_headers):
    payload = {"account_number": "ES003", "account_type": "checking", "balance": "0"}
    await client.post(
        "/api/v1/accounts",
        params={"client_id": existing_client["id"]},
        json=payload,
        headers=admin_headers,
    )
    response = await client.post(
        "/api/v1/accounts",
        params={"client_id": existing_client["id"]},
        json=payload,
        headers=admin_headers,
    )
    assert response.status_code == 409


async def test_create_account_nonexistent_client(client, admin_headers):
    response = await client.post(
        "/api/v1/accounts",
        params={"client_id": 99999},
        json={"account_number": "ES999", "account_type": "savings", "balance": "0"},
        headers=admin_headers,
    )
    assert response.status_code == 404


async def test_get_account(client, existing_client, admin_headers):
    create = await client.post(
        "/api/v1/accounts",
        params={"client_id": existing_client["id"]},
        json={"account_number": "ES004", "account_type": "investment", "balance": "5000"},
        headers=admin_headers,
    )
    account_id = create.json()["id"]
    response = await client.get(f"/api/v1/accounts/{account_id}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["id"] == account_id


async def test_get_client_with_accounts(client, existing_client, admin_headers):
    await client.post(
        "/api/v1/accounts",
        params={"client_id": existing_client["id"]},
        json={"account_number": "ES005", "account_type": "checking", "balance": "100"},
        headers=admin_headers,
    )
    response = await client.get(
        f"/api/v1/clients/{existing_client['id']}/accounts", headers=admin_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "accounts" in data
    assert len(data["accounts"]) == 1
    assert data["accounts"][0]["account_number"] == "ES005"


async def test_list_clients_paginated(client, admin_headers):
    for i in range(5):
        await client.post(
            "/api/v1/clients",
            json={"name": f"Client {i}", "email": f"client{i}@test.com"},
            headers=admin_headers,
        )
    response = await client.get(
        "/api/v1/clients", params={"page": 1, "size": 3}, headers=admin_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["size"] == 3
    assert data["total"] >= 5
    assert "pages" in data
    assert len(data["items"]) == 3


async def test_list_clients_page_size_limit(client, admin_headers):
    response = await client.get(
        "/api/v1/clients", params={"page": 1, "size": 200}, headers=admin_headers
    )
    assert response.status_code == 422


async def test_update_client(client, existing_client, admin_headers):
    response = await client.patch(
        f"/api/v1/clients/{existing_client['id']}",
        json={"name": "Updated Name"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"
    assert response.json()["email"] == existing_client["email"]


async def test_update_account_balance(client, existing_client, admin_headers):
    create = await client.post(
        "/api/v1/accounts",
        params={"client_id": existing_client["id"]},
        json={"account_number": "ES010", "account_type": "checking", "balance": "1000.00"},
        headers=admin_headers,
    )
    account_id = create.json()["id"]

    response = await client.patch(
        f"/api/v1/accounts/{account_id}",
        json={"balance": "2500.00"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert Decimal(data["balance"]) == Decimal("2500.00")
    assert data["account_number"] == "ES010"  # campo no tocado, no cambia


async def test_update_account_deactivate(client, existing_client, admin_headers):
    create = await client.post(
        "/api/v1/accounts",
        params={"client_id": existing_client["id"]},
        json={"account_number": "ES011", "account_type": "savings", "balance": "0"},
        headers=admin_headers,
    )
    account_id = create.json()["id"]

    response = await client.patch(
        f"/api/v1/accounts/{account_id}",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False


async def test_update_account_partial_fields_unchanged(client, existing_client, admin_headers):
    """PATCH solo actualiza los campos enviados, el resto permanece igual."""
    create = await client.post(
        "/api/v1/accounts",
        params={"client_id": existing_client["id"]},
        json={"account_number": "ES012", "account_type": "investment", "balance": "500.00"},
        headers=admin_headers,
    )
    original = create.json()

    response = await client.patch(
        f"/api/v1/accounts/{original['id']}",
        json={"is_active": False},
        headers=admin_headers,
    )
    data = response.json()
    assert Decimal(data["balance"]) == Decimal("500.00")  # no cambió
    assert data["account_type"] == "investment"  # no cambió
    assert data["is_active"] is False  # sí cambió


async def test_update_account_negative_balance(client, existing_client, admin_headers):
    create = await client.post(
        "/api/v1/accounts",
        params={"client_id": existing_client["id"]},
        json={"account_number": "ES013", "account_type": "checking", "balance": "100.00"},
        headers=admin_headers,
    )
    account_id = create.json()["id"]

    response = await client.patch(
        f"/api/v1/accounts/{account_id}",
        json={"balance": "-1.00"},
        headers=admin_headers,
    )
    assert response.status_code == 422


async def test_update_account_not_found(client, admin_headers):
    response = await client.patch(
        "/api/v1/accounts/99999",
        json={"balance": "100.00"},
        headers=admin_headers,
    )
    assert response.status_code == 404


async def test_update_account_requires_auth(client, existing_client, admin_headers):
    create = await client.post(
        "/api/v1/accounts",
        params={"client_id": existing_client["id"]},
        json={"account_number": "ES014", "account_type": "checking", "balance": "0"},
        headers=admin_headers,
    )
    account_id = create.json()["id"]

    response = await client.patch(
        f"/api/v1/accounts/{account_id}",
        json={"balance": "500.00"},
        # sin headers
    )
    assert response.status_code == 401


async def test_update_account_forbidden_for_viewer(
    client, existing_client, admin_headers, readonly_user
):
    login = await client.post(
        "/api/v1/auth/login",
        data={"username": readonly_user["email"], "password": readonly_user["password"]},
    )
    readonly_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    create = await client.post(
        "/api/v1/accounts",
        params={"client_id": existing_client["id"]},
        json={"account_number": "ES015", "account_type": "savings", "balance": "0"},
        headers=admin_headers,
    )
    account_id = create.json()["id"]

    response = await client.patch(
        f"/api/v1/accounts/{account_id}",
        json={"balance": "999.00"},
        headers=readonly_headers,
    )
    assert response.status_code == 403


async def test_update_account_empty_body(client, existing_client, admin_headers):
    """PATCH con body vacío no rompe nada — devuelve la cuenta sin cambios."""
    create = await client.post(
        "/api/v1/accounts",
        params={"client_id": existing_client["id"]},
        json={"account_number": "ES016", "account_type": "checking", "balance": "100.00"},
        headers=admin_headers,
    )
    account_id = create.json()["id"]

    response = await client.patch(
        f"/api/v1/accounts/{account_id}",
        json={},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert Decimal(response.json()["balance"]) == Decimal("100.00")
