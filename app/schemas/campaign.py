from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class CampaignBase(BaseModel):
    name: str
    target_amount: float
    deadline: datetime
    funding_status: Optional[str] = "active"
    regulation_type: Optional[str] = "REG_CF"
    escrow_wallet_id: Optional[str] = None
    stripe_account_id: Optional[str] = None

class CampaignCreate(CampaignBase):
    issuer_id: int

class CampaignUpdate(CampaignBase):
    name: Optional[str] = None
    target_amount: Optional[float] = None
    deadline: Optional[datetime] = None
    regulation_type: Optional[str] = None

class Campaign(CampaignBase):
    id: int
    issuer_id: int
    funding_status: str
    regulation_type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
