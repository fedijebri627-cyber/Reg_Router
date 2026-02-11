from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import schemas, models
from app.api import deps

router = APIRouter()

@router.post("/", response_model=schemas.Campaign)
def create_campaign(
    *,
    db: Session = Depends(deps.get_db),
    campaign_in: schemas.CampaignCreate,
) -> Any:
    """
    Create new campaign.
    """
    campaign = models.Campaign(
        name=campaign_in.name,
        target_amount=campaign_in.target_amount,
        deadline=campaign_in.deadline,
        funding_status=campaign_in.funding_status,
        regulation_type=campaign_in.regulation_type,
        issuer_id=campaign_in.issuer_id
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign

@router.get("/", response_model=List[schemas.Campaign])
def read_campaigns(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve campaigns.
    """
    campaigns = db.query(models.Campaign).offset(skip).limit(limit).all()
    return campaigns

@router.get("/{campaign_id}", response_model=schemas.Campaign)
def read_campaign(
    campaign_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get campaign by ID.
    """
    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign
