from datetime import datetime, timedelta
import pytest
from app.core import security

def test_auth_errors(client, override_get_db):
    # 1. Invalid Login Credentials
    res = client.post(
        "/api/v1/login/access-token",
        data={"username": "wrong@example.com", "password": "wrongpassword"}
    )
    assert res.status_code == 400
    assert "Incorrect email or password" in res.json()["detail"]

    # 2. Access Protected Endpoint without Token
    res = client.get("/api/v1/users/1")
    assert res.status_code == 401
    assert "Not authenticated" in res.json()["detail"]

    # 3. Access Protected Endpoint with Invalid Token
    headers = {"Authorization": "Bearer invalidtoken"}
    res = client.get("/api/v1/users/1", headers=headers)
    assert res.status_code == 403
    assert "Could not validate credentials" in res.json()["detail"]

def test_user_creation_errors(client, override_get_db):
    # 1. Duplicate Email
    user_data = {"email": "duplicate@example.com", "stripe_id": "cus_dup", "password": "password123"}
    client.post("/api/v1/users/", json=user_data)
    res = client.post("/api/v1/users/", json=user_data)
    assert res.status_code == 400
    assert "user with this username already exists" in res.json()["detail"]

    # 2. Invalid Email Format (Pydantic Validation)
    res = client.post(
        "/api/v1/users/",
        json={"email": "notanemail", "stripe_id": "cus_inv", "password": "password123"}
    )
    assert res.status_code == 422

    # 3. Missing Required Field
    res = client.post(
        "/api/v1/users/",
        json={"email": "missing@example.com", "stripe_id": "cus_miss"}
    )
    assert res.status_code == 422
    
def test_investment_errors(client, override_get_db):
    # Setup
    user_res = client.post("/api/v1/users/", json={"email": "invest_err@example.com", "stripe_id": "cus_inv_err", "password": "password123", "kyc_status": "unverified"})
    user_id = user_res.json()["id"]
    
    login_res = client.post("/api/v1/login/access-token", data={"username": "invest_err@example.com", "password": "password123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    camp_res = client.post("/api/v1/campaigns/", json={"name": "Inv Err Camp", "target_amount": 1000.0, "deadline": datetime.now().isoformat(), "issuer_id": 1})
    campaign_id = camp_res.json()["id"]

    # 1. Invest with Unverified KYC
    res = client.post(
        "/api/v1/ledger/invest",
        json={"user_id": user_id, "campaign_id": campaign_id, "amount": 100.0, "transaction_type": "investment"},
        headers=headers
    )
    assert res.status_code == 403
    assert "unverified" in res.json()["detail"] or "KYC" in res.json()["detail"]

    # 2. Invest in Non-Existent Campaign
    res = client.post(
        "/api/v1/ledger/invest",
        json={"user_id": user_id, "campaign_id": 99999, "amount": 100.0, "transaction_type": "investment"},
        headers=headers
    )
    assert res.status_code == 404
    assert "Campaign not found" in res.json()["detail"]

    # 3. Authorization: Invest for Another User
    other_user_res = client.post("/api/v1/users/", json={"email": "other@example.com", "stripe_id": "cus_other", "password": "password123"})
    other_id = other_user_res.json()["id"]
    
    res = client.post(
        "/api/v1/ledger/invest",
        json={"user_id": other_id, "campaign_id": campaign_id, "amount": 100.0, "transaction_type": "investment"},
        headers=headers
    )
    assert res.status_code == 403
    assert "Not authorized" in res.json()["detail"]
