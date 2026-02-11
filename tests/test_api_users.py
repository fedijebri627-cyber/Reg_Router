import pytest
from app import schemas

def test_create_user(client, override_get_db):
    response = client.post(
        "/api/v1/users/",
        json={"email": "test@example.com", "stripe_id": "cus_123", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

def test_read_user(client, override_get_db):
    # Create user first
    response = client.post(
        "/api/v1/users/",
        json={"email": "read@example.com", "stripe_id": "cus_456", "password": "password123"},
    )
    user_id = response.json()["id"]

    # Read user
    # Login to get token
    login_res = client.post(
        "/api/v1/login/access-token",
        data={"username": "read@example.com", "password": "password123"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(f"/api/v1/users/{user_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "read@example.com"

def test_update_kyc(client, override_get_db):
    # Create user
    response = client.post(
        "/api/v1/users/",
        json={"email": "kyc@example.com", "stripe_id": "cus_789", "password": "password123"},
    )
    user_id = response.json()["id"]

    # Login to get token
    login_res = client.post(
        "/api/v1/login/access-token",
        data={"username": "kyc@example.com", "password": "password123"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Update KYC
    response = client.post(f"/api/v1/users/{user_id}/kyc?kyc_status=verified", headers=headers)
    assert response.status_code == 200
    assert response.json()["kyc_status"] == "verified"
