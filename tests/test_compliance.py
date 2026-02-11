import pytest
from datetime import datetime, timedelta, timezone
from app.schemas.user import User
from app.schemas.campaign import Campaign
from app.services.compliance import ComplianceService

# Mock Data
def create_mock_user(kyc_status="unverified"):
    return User(
        id=1,
        stripe_id="cus_123",
        email="test@example.com",
        kyc_status=kyc_status,
        is_accredited=False,
        created_at=datetime.now(timezone.utc)
    )

def create_mock_campaign(target_amount=10000.0):
    return Campaign(
        id=1,
        name="Test Campaign",
        issuer_id=1,
        target_amount=target_amount,
        deadline=datetime.now(timezone.utc) + timedelta(days=30),
        funding_status="active",
        regulation_type="REG_CF",
        created_at=datetime.now(timezone.utc)
    )

# Tests
def test_kyc_validation():
    user = create_mock_user(kyc_status="verified")
    assert ComplianceService.check_kyc(user) is True

    user_unverified = create_mock_user(kyc_status="unverified")
    assert ComplianceService.check_kyc(user_unverified) is False

def test_lockup_period():
    # Transaction date 1 year and 1 day ago (Allowed)
    past_date = datetime.now(timezone.utc) - timedelta(days=366)
    assert ComplianceService.check_lockup_period(past_date) is True

    # Transaction date 1 day ago (Restricted)
    recent_date = datetime.now(timezone.utc) - timedelta(days=1)
    assert ComplianceService.check_lockup_period(recent_date) is False

def test_escrow_threshold():
    campaign = create_mock_campaign(target_amount=10000.0)
    
    # Fully funded
    assert ComplianceService.check_escrow_threshold(campaign, 10000.0) is True
    assert ComplianceService.check_escrow_threshold(campaign, 15000.0) is True
    
    # Underfunded
    assert ComplianceService.check_escrow_threshold(campaign, 5000.0) is False
