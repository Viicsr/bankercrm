def test_404_returns_standard_format(client, admin_headers):
    response = client.get("/api/v1/clients/99999", headers=admin_headers)
    assert response.status_code == 404
    data = response.json()
    # Verifica el formato estandarizado
    assert "error" in data
    assert "detail" in data
    assert "path" in data
    assert data["error"] == "NotFoundError"
    assert "/clients/99999" in data["path"]


def test_409_on_duplicate_email(client, admin_headers):
    payload = {"name": "Victor", "email": "dup@test.com"}
    client.post("/api/v1/clients", json=payload, headers=admin_headers)
    response = client.post("/api/v1/clients", json=payload, headers=admin_headers)
    assert response.status_code == 409
    assert response.json()["error"] == "ConflictError"


def test_422_validation_error_format(client, admin_headers):
    response = client.post(
        "/api/v1/clients",
        json={"name": "Test", "email": "not-an-email"},
        headers=admin_headers,
    )
    assert response.status_code == 422
    data = response.json()
    assert data["error"] == "ValidationError"
    assert "errors" in data
    assert isinstance(data["errors"], list)
    assert len(data["errors"]) > 0
    assert "field" in data["errors"][0]
    assert "message" in data["errors"][0]


def test_401_returns_standard_format(client):
    response = client.get("/api/v1/clients")
    assert response.status_code == 401


def test_403_returns_standard_format(client, readonly_user):
    from tests.test_auth import get_auth_headers
    headers = get_auth_headers(client, readonly_user["email"], readonly_user["password"])
    response = client.post(
        "/api/v1/clients",
        json={"name": "Forbidden", "email": "forbidden@test.com"},
        headers=headers,
    )
    assert response.status_code == 403
    assert response.json()["error"] == "ForbiddenError"

def test_invalid_path_returns_404(client):
    response = client.get("/api/v1/ruta_que_no_existe")
    assert response.status_code == 404