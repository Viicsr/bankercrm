import pytest


async def get_auth_headers(client, email: str, password: str) -> dict:
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_register_user(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "new@test.com", "password": "Pass1234!"},
    )
    assert response.status_code == 201
    assert response.json()["email"] == "new@test.com"
    assert response.json()["role"] == "read_only"
    assert "hashed_password" not in response.json()


async def test_register_duplicate_email(client, admin_user):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": admin_user["email"], "password": "OtroPass1!"},
    )
    assert response.status_code == 409


async def test_login_success(client, admin_user):
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": admin_user["email"], "password": admin_user["password"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client, admin_user):
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": admin_user["email"], "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert "email or password" in response.json()["detail"].lower()


async def test_login_nonexistent_email(client):
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "noexiste@test.com", "password": "cualquiera"},
    )
    assert response.status_code == 401
    assert "email or password" in response.json()["detail"].lower()


async def test_protected_endpoint_without_token(client):
    response = await client.post(
        "/api/v1/clients",
        json={"name": "Test", "email": "t@test.com"},
    )
    assert response.status_code == 401


async def test_protected_endpoint_with_invalid_token(client):
    response = await client.post(
        "/api/v1/clients",
        json={"name": "Test", "email": "t@test.com"},
        headers={"Authorization": "Bearer token_inventado_invalido"},
    )
    assert response.status_code == 401


async def test_admin_can_create_client(client, admin_user):
    headers = await get_auth_headers(client, admin_user["email"], admin_user["password"])
    response = await client.post(
        "/api/v1/clients",
        json={"name": "Admin Client", "email": "adminclient@bank.com"},
        headers=headers,
    )
    assert response.status_code == 201


async def test_readonly_cannot_create_client(client, readonly_user):
    headers = await get_auth_headers(client, readonly_user["email"], readonly_user["password"])
    response = await client.post(
        "/api/v1/clients",
        json={"name": "Readonly Client", "email": "ro@bank.com"},
        headers=headers,
    )
    assert response.status_code == 403


async def test_readonly_can_read_clients(client, admin_user, readonly_user):
    admin_hdrs = await get_auth_headers(client, admin_user["email"], admin_user["password"])
    await client.post(
        "/api/v1/clients",
        json={"name": "Visible Client", "email": "visible@bank.com"},
        headers=admin_hdrs,
    )
    ro_headers = await get_auth_headers(client, readonly_user["email"], readonly_user["password"])
    response = await client.get("/api/v1/clients", headers=ro_headers)
    assert response.status_code == 200


async def test_refresh_token(client, admin_user):
    login = await client.post(
        "/api/v1/auth/login",
        data={"username": admin_user["email"], "password": admin_user["password"]},
    )
    refresh_token = login.json()["refresh_token"]
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_refresh_with_access_token_fails(client, admin_user):
    login = await client.post(
        "/api/v1/auth/login",
        data={"username": admin_user["email"], "password": admin_user["password"]},
    )
    access_token = login.json()["access_token"]
    # El access token NO debe funcionar como refresh token
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": access_token},
    )
    assert response.status_code == 401
