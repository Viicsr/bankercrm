import pytest
from decimal import Decimal

# Fixture reutilizable — crea un cliente base para los tests de accounts
@pytest.fixture
def existing_client(client):
    response = client.post(
        "/api/v1/clients",
        json={"name": "Test Client", "email": "accounts@test.com"}
    )
    assert response.status_code == 201
    return response.json()

def test_create_account(client, existing_client):
    response = client.post(
        "/api/v1/accounts",
        params={"client_id": existing_client["id"]},
        json={
            "account_number": "ES001",
            "account_type": "checking",
            "balance": "1000.00"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["account_number"] == "ES001"
    assert data["client_id"] == existing_client["id"]
    assert Decimal(data["balance"]) == Decimal("1000.00")

def test_create_account_negative_balance(client, existing_client):
    response = client.post(
        "/api/v1/accounts",
        params={"client_id": existing_client["id"]},
        json={
            "account_number": "ES002",
            "account_type": "savings",
            "balance": "-50.00"
        }
    )
    assert response.status_code == 422  # Pydantic validation error

def test_create_account_duplicate_number(client, existing_client):
    payload = {"account_number": "ES003", "account_type": "checking", "balance": "0"}
    client.post("/api/v1/accounts", params={"client_id": existing_client["id"]}, json=payload)
    response = client.post("/api/v1/accounts", params={"client_id": existing_client["id"]}, json=payload)
    assert response.status_code == 409  # ValueError del service

def test_create_account_nonexistent_client(client):
    response = client.post(
        "/api/v1/accounts",
        params={"client_id": 99999},
        json={"account_number": "ES999", "account_type": "savings", "balance": "0"}
    )
    assert response.status_code == 404

def test_get_account(client, existing_client):
    create = client.post(
        "/api/v1/accounts",
        params={"client_id": existing_client["id"]},
        json={"account_number": "ES004", "account_type": "investment", "balance": "5000"}
    )
    account_id = create.json()["id"]
    response = client.get(f"/api/v1/accounts/{account_id}")
    assert response.status_code == 200
    assert response.json()["id"] == account_id

def test_get_client_with_accounts(client, existing_client):
    client.post(
        "/api/v1/accounts",
        params={"client_id": existing_client["id"]},
        json={"account_number": "ES005", "account_type": "checking", "balance": "100"}
    )
    response = client.get(f"/api/v1/clients/{existing_client['id']}/accounts")
    assert response.status_code == 200
    data = response.json()
    assert "accounts" in data
    assert len(data["accounts"]) == 1
    assert data["accounts"][0]["account_number"] == "ES005"

def test_list_clients_paginated(client):
    for i in range(5):
        client.post(
            "/api/v1/clients",
            json={"name": f"Client {i}", "email": f"client{i}@test.com"}
        )
    response = client.get("/api/v1/clients", params={"page": 1, "size": 3})
    assert response.status_code == 200
    data = response.json()
    assert data["size"] == 3
    assert data["total"] >= 5
    assert "pages" in data
    assert len(data["items"]) == 3

def test_list_clients_page_size_limit(client):
    response = client.get("/api/v1/clients", params={"page": 1, "size": 200})
    assert response.status_code == 422

def test_update_client(client, existing_client):
    response = client.patch(
        f"/api/v1/clients/{existing_client['id']}",
        json={"name": "Updated Name"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"
    assert response.json()["email"] == existing_client["email"]  # no cambia