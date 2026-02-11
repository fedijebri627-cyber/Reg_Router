from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
from sqlalchemy.sql import func
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    stripe_id = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    kyc_status = Column(String, default="unverified") # unverified, pending, verified
    is_accredited = Column(Boolean, default=False)
    net_worth = Column(Float, nullable=True)
    annual_income = Column(Float, nullable=True)
    annual_income = Column(Float, nullable=True)
    
    # Accreditation & Compliance
    accreditation_status = Column(String, default="NONE") # NONE, SELF_CERTIFIED, PENDING_REVIEW, VERIFIED_DOCS
    accreditation_expiry = Column(DateTime(timezone=True), nullable=True)
    accreditation_verified_at = Column(DateTime(timezone=True), nullable=True)
    accreditation_verified_by = Column(Integer, nullable=True) # Admin ID

    stripe_connect_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
