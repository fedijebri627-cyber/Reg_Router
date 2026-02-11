import pytest
from datetime import datetime, timedelta

def test_invest_compliance(client, override_get_db):
    # 1. Create User (Unverified)
    user_res = client.post(
        "/api/v1/users/",
        json={"email": "investor@example.com", "stripe_id": "cus_inv", "kyc_status": "unverified", "password": "password123"},
    )
    user_id = user_res.json()["id"]

    # 1.1 Login
    login_res = client.post(
        "/api/v1/login/access-token",
        data={"username": "investor@example.com", "password": "password123"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Campaign
    camp_res = client.post(
        "/api/v1/campaigns/",
        json={
            "name": "Invest Campaign",
            "target_amount": 10000.0,
            "deadline": (datetime.now() + timedelta(days=30)).isoformat(),
            "issuer_id": 1
        },
    )
    campaign_id = camp_res.json()["id"]

    # 3. Try to Invest (Should Fail: KYC)
    res = client.post(
        "/api/v1/ledger/invest",
        json={
            "user_id": user_id,
            "campaign_id": campaign_id,
            "amount": 1000.0,
            "transaction_type": "investment"
        },
        headers=headers
    )
    assert res.status_code == 403
    assert "KYC" in res.json()["detail"]

    # 4. Verify User
    kyc_res = client.post(f"/api/v1/users/{user_id}/kyc?kyc_status=verified", headers=headers)
    assert kyc_res.status_code == 200

    # 5. Try to Invest (Should Pass)
    from unittest.mock import MagicMock, patch
    with patch("app.services.stripe_service.StripeService.create_payment_intent") as mock_stripe:
        mock_stripe.return_value = MagicMock(id="pi_mock", client_secret="secret_mock")
        
        res = client.post(
            "/api/v1/ledger/invest",
            json={
                "user_id": user_id,
                "campaign_id": campaign_id,
                "amount": 1000.0,
                "transaction_type": "investment"
            },
            headers=headers
        )
    assert res.status_code == 200
    assert res.json()["status"] == "pending_payment"

def test_trade_lockup(client, override_get_db):
    # Setup: User & Campaign
    user_res = client.post("/api/v1/users/", json={"email": "trader@example.com", "stripe_id": "cus_trd", "password": "password123"})
    user_id = user_res.json()["id"]

    # Login
    login_res = client.post(
        "/api/v1/login/access-token",
        data={"username": "trader@example.com", "password": "password123"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    camp_res = client.post("/api/v1/campaigns/", json={"name": "Trade Camp", "target_amount": 1000.0, "deadline": datetime.now().isoformat(), "issuer_id": 1})
    campaign_id = camp_res.json()["id"]

    # 1. Try Trade with recent original transaction (Should Fail)
    recent_date = (datetime.now() - timedelta(days=10)).isoformat()
    res = client.post(
        f"/api/v1/ledger/trade?original_transaction_date={recent_date}",
        json={
            "user_id": user_id,
            "campaign_id": campaign_id,
            "amount": 100.0,
            "transaction_type": "trade"
        },
        headers=headers
    )
    assert res.status_code == 403
    assert "lockup" in res.json()["detail"]

    # 2. Try Trade with old original transaction (Should Pass)
    old_date = (datetime.now() - timedelta(days=400)).isoformat()
    res = client.post(
        f"/api/v1/ledger/trade?original_transaction_date={old_date}",
        json={
            "user_id": user_id,
            "campaign_id": campaign_id,
            "amount": 100.0,
            "transaction_type": "trade"
        },
        headers=headers
    )
    # Note: It might fail if User/Campaign logic in /trade endpoint is stricter, but based on code it just checks lockup and creates ledger
    assert res.status_code == 200
