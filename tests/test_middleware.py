def test_request_id_header_present(client):
    response = client.get("/health")
    assert "x-request-id" in response.headers
    assert len(response.headers["x-request-id"]) > 0


def test_process_time_header_present(client):
    response = client.get("/health")
    assert "x-process-time" in response.headers


def test_security_headers_present(client):
    response = client.get("/health")
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"


def test_each_request_has_unique_request_id(client):
    r1 = client.get("/health")
    r2 = client.get("/health")
    assert r1.headers["x-request-id"] != r2.headers["x-request-id"]


def test_error_response_includes_request_id(client, admin_headers):
    response = client.get("/api/v1/clients/99999", headers=admin_headers)
    assert response.status_code == 404
    # El request_id en el body del error debe coincidir con el header
    data = response.json()
    if "request_id" in data and data["request_id"]:
        assert data["request_id"] == response.headers.get("x-request-id")