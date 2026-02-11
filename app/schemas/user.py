from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict

class UserBase(BaseModel):
    email: EmailStr
    kyc_status: Optional[str] = "unverified"
    is_accredited: Optional[bool] = False
    net_worth: Optional[float] = None
    annual_income: Optional[float] = None

class UserCreate(UserBase):
    stripe_id: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserUpdate(UserBase):
    stripe_id: Optional[str] = None
    email: Optional[EmailStr] = None
    net_worth: Optional[float] = None
    annual_income: Optional[float] = None
    accreditation_status: Optional[str] = "NONE"
    accreditation_expiry: Optional[datetime] = None
    accreditation_verified_at: Optional[datetime] = None
    stripe_connect_id: Optional[str] = None
    stripe_connect_id: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class User(UserBase):
    id: int
    stripe_id: str
    stripe_connect_id: Optional[str] = None
    accreditation_status: Optional[str] = "NONE"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
