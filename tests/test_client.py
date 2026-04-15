def test_create_client(client, admin_headers):
    response = client.post(
        "/api/v1/clients",
        json={"name": "Victor", "email": "victor@test.com"},
        headers=admin_headers,
    )
    assert response.status_code == 201

def test_create_client_duplicate_email(client, admin_headers):
    client.post("/api/v1/clients", json={"name": "Victor", "email": "victor@test.com"},headers=admin_headers)
    response = client.post("/api/v1/clients", json={"name": "Otro", "email": "victor@test.com"}, headers=admin_headers)
    assert response.status_code == 409

def test_get_client(client,admin_headers):
    create = client.post("/api/v1/clients", json={"name": "Victor", "email": "victor@test.com"},headers=admin_headers)
    client_id = create.json()["id"]
    response = client.get(f"/api/v1/clients/{client_id}",headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["id"] == client_id

def test_get_client_not_found(client, admin_headers):
    response = client.get("/api/v1/clients/99999",headers=admin_headers)
    assert response.status_code == 404