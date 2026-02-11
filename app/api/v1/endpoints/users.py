from typing import Any, List
import logging
from fastapi import APIRouter, Body, Depends, HTTPException, UploadFile, File
from fastapi.encoders import jsonable_encoder
from pydantic.networks import EmailStr
from sqlalchemy.orm import Session
from app import models, schemas
from app.api import deps
from app.core.config import settings
from datetime import datetime # Ensure deps is imported if not already

router = APIRouter()

from app.core import security
# from app.api import deps # Ensure deps is imported if not already - This line is redundant after the import block update

@router.post("/me/accreditation/upload", response_model=schemas.User)
def upload_accreditation(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
    file: UploadFile = File(...)
) -> Any:
    """
    Upload accreditation proof (PDF).
    Updates status to PENDING_REVIEW.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")
    
    # Mock S3 Upload: In prod, upload to S3 and save URL
    logging.info(f"Mocking upload of {file.filename} for user {current_user.id}")
    
    current_user.accreditation_status = "PENDING_REVIEW"
    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/", response_model=schemas.User)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate,
) -> Any:
    """
    Create new user.
    """
    user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = models.User(
        email=user_in.email,
        hashed_password=security.get_password_hash(user_in.password),
        stripe_id=user_in.stripe_id,
        kyc_status=user_in.kyc_status,
        is_accredited=user_in.is_accredited,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.get("/{user_id}", response_model=schemas.User)
def read_user(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get user by ID.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/{user_id}/kyc", response_model=schemas.User)
def update_kyc_status(
    user_id: int,
    kyc_status: str,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Update KYC status (Simulated).
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.kyc_status = kyc_status
    db.commit()
    db.refresh(user)
    return user
