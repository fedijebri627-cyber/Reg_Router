from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base

class BillingLog(Base):
    __tablename__ = "billing_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id")) # Platform/User being billed
    transaction_id = Column(String, index=True) # Check ID or Ledger ID
    fee_amount = Column(Float, default=2.00)
    description = Column(String) # e.g. "Validation Check: Reg D 506(c)"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
