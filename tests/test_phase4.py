
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import pytest
from app import models, schemas
from app.api.deps import get_current_user

# Mocks
@pytest.fixture
def mock_stripe_service():
    with patch("app.services.stripe_service.StripeService") as mock: # Patch where it is defined
        mock.create_payment_intent.return_value = MagicMock(
            id="pi_mock_123",
            client_secret="secret_mock_123"
        )
        yield mock

@pytest.fixture
def mock_stripe_refund():
    with patch("app.services.stripe_service.StripeService") as mock: # Patch where it is defined
        mock.refund_payment.return_value = MagicMock(status="succeeded")
        yield mock

@pytest.fixture
def mock_worker_task():
    with patch("app.api.v1.endpoints.ledger.settle_investment_task") as mock:
        yield mock

@pytest.fixture
def normal_user_token_headers(client, override_get_db):
    email = "phase4@example.com"
    password = "password123"
    # Create User
    client.post(
        "/api/v1/users/",
        json={"email": email, "stripe_id": "cus_phase4", "password": password},
    )
    # Login
    r = client.post(
        "/api/v1/login/access-token",
        data={"username": email, "password": password}
    )
    tokens = r.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}

def test_investment_limit_exceeded(client, override_get_db, normal_user_token_headers, db):
    # User has low income/net worth
    
    # 1. Update user financial info manually in DB using the SHARED session
    user = db.query(models.User).filter(models.User.email == "phase4@example.com").first()
    # Ensure user exists (created by fixture)
    if not user:
         pytest.fail("Test user not found")
         
    user.annual_income = 50000
    user.net_worth = 50000
    user.kyc_status = "verified"
    db.commit() # Commit to save changes for the API call (shared session)
    
    # 2. Create Campaign
    res = client.post(
        "/api/v1/campaigns/",
        json={
            "name": "Limit Test Campaign",
            "target_amount": 100000,
            "deadline": (datetime.now() + timedelta(days=30)).isoformat(),
            "issuer_id": 1
        }
    )
    campaign_id = res.json()["id"]

    # 3. Invest 3000 (Should Fail)
    res = client.post(
        "/api/v1/ledger/invest",
        json={
            "user_id": user.id,
            "campaign_id": campaign_id,
            "amount": 3000.0,
            "transaction_type": "investment"
        },
        headers=normal_user_token_headers
    )
    assert res.status_code == 403
    assert "exceeds SEC" in res.json()["detail"]

def test_investment_success_with_stripe(client, override_get_db, normal_user_token_headers, mock_stripe_service, db, mock_worker_task):
    # Invest 1000 (Within limit)
    
    # Setup User & Campaign (re-using checking user from prev test or new)
    # We rely on DB state reset or clean data. 
    # For simplicity, assume user is same and limit is 2500. 1000 is fine.
    
    # Get User ID
    res = client.get("/api/v1/users/me", headers=normal_user_token_headers)
    # Since /users/me might not exist, let's look it up via DB
    user = db.query(models.User).filter(models.User.email == "phase4@example.com").first()
    user.kyc_status = "verified"
    user.annual_income = 100000
    user.net_worth = 100000
    db.commit()
    user_id = user.id 

    # Campaign
    res = client.post(
        "/api/v1/campaigns/",
        json={
            "name": "Stripe Test Campaign",
            "target_amount": 100000,
            "deadline": (datetime.now() + timedelta(days=30)).isoformat(),
            "issuer_id": 1
        }
    )
    campaign_id = res.json()["id"]

    res = client.post(
        "/api/v1/ledger/invest",
        json={
            "user_id": user_id,
            "campaign_id": campaign_id,
            "amount": 1000.0,
            "transaction_type": "investment"
        },
        headers=normal_user_token_headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "pending_payment"
    assert data["stripe_payment_intent_id"] == "pi_mock_123"
    assert data["client_secret"] == "secret_mock_123"
    
def test_cancellation_window_closed(client, override_get_db, normal_user_token_headers, db, mock_worker_task):
    # Create Campaign ending in 1 hour (Window closed)
    res = client.post(
        "/api/v1/campaigns/",
        json={
            "name": "Late Campaign",
            "target_amount": 100000,
            "deadline": (datetime.now() + timedelta(hours=1)).isoformat(),
            "issuer_id": 1
        }
    )
    campaign_id = res.json()["id"]
    
    # Need to create an investment manually in DB because /invest might fail limit or need stripe mock
    # OR helper to create investment
    user = db.query(models.User).filter(models.User.email == "phase4@example.com").first()
    ledger = models.Ledger(
        user_id=user.id, # normal user
        campaign_id=campaign_id,
        amount=500,
        transaction_type="investment",
        status="pending_settlement"
    )
    db.add(ledger)
    db.commit()
    db.refresh(ledger)
    ledger_id = ledger.id

    # Try Cancel
    res = client.post(f"/api/v1/ledger/investments/{ledger_id}/cancel", headers=normal_user_token_headers)
    assert res.status_code == 403
    assert "Cancellation window closed" in res.json()["detail"]

def test_cancellation_success(client, override_get_db, normal_user_token_headers, mock_stripe_refund, db, mock_worker_task):
    # Campaign ending in 30 days
    res = client.post(
        "/api/v1/campaigns/",
        json={
            "name": "Cancelable Campaign",
            "target_amount": 100000,
            "deadline": (datetime.now() + timedelta(days=30)).isoformat(),
            "issuer_id": 1
        }
    )
    campaign_id = res.json()["id"]

    # Create Investment
    user = db.query(models.User).filter(models.User.email == "phase4@example.com").first()
    ledger = models.Ledger(
        user_id=user.id,
        campaign_id=campaign_id,
        amount=500,
        transaction_type="investment",
        status="pending_payment",
        stripe_payment_intent_id="pi_to_refund"
    )
    db.add(ledger)
    db.commit()
    db.refresh(ledger)
    ledger_id = ledger.id

    # Cancel
    res = client.post(f"/api/v1/ledger/investments/{ledger_id}/cancel", headers=normal_user_token_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "cancelled"
    # Mock should be called
    # assert mock_stripe_refund.called # Need to check mock object
