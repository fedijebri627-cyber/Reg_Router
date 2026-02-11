import pytest
from datetime import datetime, timedelta
from app import models
from unittest.mock import MagicMock, patch
import uuid

def test_reg_cf_invest_success(client, override_get_db, db):
    # Setup Reg CF Campaign
    res = client.post("/api/v1/campaigns/", json={
        "name": f"Reg CF Deal {uuid.uuid4()}", "target_amount": 10000, "deadline": (datetime.now() + timedelta(days=30)).isoformat(), "issuer_id": 1,
        "regulation_type": "REG_CF"
    })
    campaign_id = res.json()["id"]

    # Create & Verify User
    email = f"cf_investor_{uuid.uuid4()}@example.com"
    res = client.post("/api/v1/users/", json={"email": email, "stripe_id": f"cus_{uuid.uuid4()}", "password": "password123"})
    user_id = res.json()["id"]
    
    # Login
    login_res = client.post("/api/v1/login/access-token", data={"username": email, "password": "password123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify User for KYC
    user = db.query(models.User).filter(models.User.id == user_id).first()
    user.kyc_status = "verified"
    user.annual_income = 100000
    user.net_worth = 100000
    db.commit()

    # Invest (Mock Stripe)
    with patch("app.services.stripe_service.StripeService.create_payment_intent") as mock_stripe:
        mock_stripe.return_value = MagicMock(id="pi_cf", client_secret="secret_cf")
        res = client.post("/api/v1/ledger/invest", json={
            "user_id": user.id, "campaign_id": campaign_id, "amount": 1000.0, "transaction_type": "investment"
        }, headers=headers)
    
    assert res.status_code == 200, res.text
    # Check Billing
    log = db.query(models.BillingLog).filter(models.BillingLog.description.contains("REG_CF")).first()
    assert log is not None
    assert log.fee_amount == 2.0

def test_reg_506b_cooloff_fail(client, override_get_db, db):
    # Create New User (Today)
    email = f"newbie_{uuid.uuid4()}@example.com"
    res = client.post("/api/v1/users/", json={"email": email, "stripe_id": f"cus_{uuid.uuid4()}", "password": "password123"})
    assert res.status_code == 200, res.text
    user_id = res.json()["id"]
    
    token = client.post("/api/v1/login/access-token", data={"username": email, "password": "password123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Setup 506(b) Campaign
    res = client.post("/api/v1/campaigns/", json={
        "name": f"Private Deal {uuid.uuid4()}", "target_amount": 10000, "deadline": (datetime.now() + timedelta(days=30)).isoformat(), "issuer_id": 1,
        "regulation_type": "506_B"
    })
    campaign_id = res.json()["id"]

    # Invest -> Should Fail (Cool-off)
    res = client.post("/api/v1/ledger/invest", json={
        "user_id": user_id, "campaign_id": campaign_id, "amount": 50000.0, "transaction_type": "investment"
    }, headers=headers)
    
    assert res.status_code == 403
    assert "known >30 days" in res.json()["detail"]

def test_reg_506c_verification_fail(client, override_get_db, db):
    # Create User
    email = f"richdoc_{uuid.uuid4()}@example.com"
    res = client.post("/api/v1/users/", json={"email": email, "stripe_id": f"cus_{uuid.uuid4()}", "password": "password123"})
    assert res.status_code == 200, res.text
    user_id = res.json()["id"]
    token = client.post("/api/v1/login/access-token", data={"username": email, "password": "password123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Setup 506(c) Campaign
    res = client.post("/api/v1/campaigns/", json={
        "name": f"Public Deal {uuid.uuid4()}", "target_amount": 10000, "deadline": (datetime.now() + timedelta(days=30)).isoformat(), "issuer_id": 1,
        "regulation_type": "506_C"
    })
    campaign_id = res.json()["id"]

    # Invest -> Should Fail (Not Verified)
    res = client.post("/api/v1/ledger/invest", json={
        "user_id": user_id, "campaign_id": campaign_id, "amount": 100000.0, "transaction_type": "investment"
    }, headers=headers)
    
    assert res.status_code == 403
    assert "Verified by Admin" in res.json()["detail"]

def test_reg_506c_success_after_admin_verify(client, override_get_db, db):
    # Create New User
    email = f"richdoc_success_{uuid.uuid4()}@example.com"
    res = client.post("/api/v1/users/", json={"email": email, "stripe_id": f"cus_{uuid.uuid4()}", "password": "password123"})
    user = db.query(models.User).filter(models.User.email == email).first()
    
    token = client.post("/api/v1/login/access-token", data={"username": email, "password": "password123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Admin Verify
    admin_token = token # Simulating admin
    res = client.post(f"/api/v1/admin/users/{user.id}/verify", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert res.json()["accreditation_status"] == "VERIFIED_DOCS"

    # Create 506(c) Campaign for this test
    res = client.post("/api/v1/campaigns/", json={
        "name": f"Public Deal Success {uuid.uuid4()}", "target_amount": 10000, "deadline": (datetime.now() + timedelta(days=30)).isoformat(), "issuer_id": 1,
        "regulation_type": "506_C"
    })
    campaign_id = res.json()["id"]

    # Invest -> Should Success
    with patch("app.services.stripe_service.StripeService.create_payment_intent") as mock_stripe:
        mock_stripe.return_value = MagicMock(id="pi_506c", client_secret="secret_506c")
        res = client.post("/api/v1/ledger/invest", json={
            "user_id": user.id, "campaign_id": campaign_id, "amount": 100000.0, "transaction_type": "investment"
        }, headers=headers)

    assert res.status_code == 200
    # Check Billing
    log = db.query(models.BillingLog).filter(models.BillingLog.description.contains("506_C")).first()
    assert log is not None
