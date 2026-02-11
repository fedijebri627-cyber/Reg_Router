from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.db.base import Base

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    issuer_id = Column(Integer, index=True) # FK to User
    target_amount = Column(Float)
    deadline = Column(DateTime(timezone=True))
    funding_status = Column(String, default="active") # active, funded, failed
    regulation_type = Column(String, default="REG_CF") # REG_CF, 506_B, 506_C
    escrow_wallet_id = Column(String, nullable=True)
    stripe_account_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
