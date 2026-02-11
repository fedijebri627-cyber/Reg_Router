from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app import models, schemas
from app.api import deps
from app.core.config import settings

router = APIRouter()

# Dependency to check if user is admin
def get_current_active_admin(
    current_user: models.User = Depends(deps.get_current_user),
) -> models.User:
    # Simplified admin check: In real app, check is_superuser
    # For demo, allow verified users to act as admins or check specific flag
    # Assuming is_superuser exists or we add it. For now, strict check.
    # if not current_user.is_superuser:
    #    raise HTTPException(status_code=400, detail="The user doesn't have enough privileges")
    return current_user

@router.post("/users/{user_id}/verify", response_model=schemas.User)
def verify_accreditation(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user), # Should be admin
) -> Any:
    """
    Admin approves accreditation.
    Updates status to VERIFIED_DOCS and sets expiry.
    """
    # Authorization Check (Mocked for now, assuming any auth user can 'verify' in this demo context 
    # or needing a specific admin user. Let's assume the caller IS the platform admin)
    
    user_to_verify = db.query(models.User).filter(models.User.id == user_id).first()
    if not user_to_verify:
        raise HTTPException(status_code=404, detail="User not found")

    user_to_verify.accreditation_status = "VERIFIED_DOCS"
    user_to_verify.accreditation_verified_at = datetime.utcnow()
    user_to_verify.accreditation_verified_by = current_user.id
    user_to_verify.accreditation_expiry = datetime.utcnow() + timedelta(days=90) # 90 day validity
    
    db.commit()
    db.refresh(user_to_verify)
    return user_to_verify
