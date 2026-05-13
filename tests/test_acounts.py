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
