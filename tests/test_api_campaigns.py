import pytest
from datetime import datetime, timedelta

def test_create_campaign(client, override_get_db):
    response = client.post(
        "/api/v1/campaigns/",
        json={
            "name": "Test Campaign",
            "target_amount": 10000.0,
            "deadline": (datetime.now() + timedelta(days=30)).isoformat(),
            "issuer_id": 1,
            "funding_status": "active"
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Campaign"
    assert "id" in data

def test_read_campaigns(client, override_get_db):
    # Create campaign
    client.post(
        "/api/v1/campaigns/",
        json={
            "name": "List Campaign",
            "target_amount": 5000.0,
            "deadline": (datetime.now() + timedelta(days=30)).isoformat(),
            "issuer_id": 1
        },
    )
    
    response = client.get("/api/v1/campaigns/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
