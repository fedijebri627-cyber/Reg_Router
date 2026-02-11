from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class LedgerBase(BaseModel):
    amount: float
    transaction_type: str
    status: Optional[str] = "pending_settlement"

class LedgerCreate(LedgerBase):
    user_id: int
    campaign_id: int

class LedgerUpdate(LedgerBase):
    status: Optional[str] = None

class Ledger(LedgerBase):
    id: int
    user_id: int
    campaign_id: int
    stripe_payment_intent_id: Optional[str] = None
    client_secret: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
