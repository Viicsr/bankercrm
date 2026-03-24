def test_create_client(client):
    response = client.post("/api/v1/clients", json={"name": "Victor", "email": "victor@test.com"})
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "victor@test.com"
    assert data["is_active"] is True
    assert "id" in data

def test_create_client_duplicate_email(client):
    client.post("/api/v1/clients", json={"name": "Victor", "email": "victor@test.com"})
    response = client.post("/api/v1/clients", json={"name": "Otro", "email": "victor@test.com"})
    assert response.status_code == 409

def test_get_client(client):
    create = client.post("/api/v1/clients", json={"name": "Victor", "email": "victor@test.com"})
    client_id = create.json()["id"]
    response = client.get(f"/api/v1/clients/{client_id}")
    assert response.status_code == 200
    assert response.json()["id"] == client_id

def test_get_client_not_found(client):
    response = client.get("/api/v1/clients/99999")
    assert response.status_code == 404