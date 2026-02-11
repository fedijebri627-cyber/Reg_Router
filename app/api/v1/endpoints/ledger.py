from typing import Any, List
from sqlalchemy import func
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app import schemas, models
from app.api import deps
from app.services.compliance import ComplianceService
from app.worker import settle_investment_task
from app.services.email_service import EmailService

router = APIRouter()

@router.post("/invest", response_model=schemas.Ledger)
def create_investment(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
    investment_in: schemas.LedgerCreate,
) -> Any:
    """
    Create investment (Compliance Router + Turnstile).
    """
    # Verify the user is investing for themselves (Implicit via Token)
    user = current_user
    investment_in__user_id = user.id # Explicitly bind ID from token
    campaign = db.query(models.Campaign).filter(models.Campaign.id == investment_in.campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # --- TRAFFIC COP LOGIC (Compliance Router) ---
    is_compliant = False
    
    # Lane A: Reg CF
    if campaign.regulation_type == "REG_CF":
        # 1. KYC Check
        if not ComplianceService.check_kyc(user):
            raise HTTPException(status_code=403, detail="User is not KYC verified")
            
        # 2. Investment Limits (SEC § 227.100)
        from datetime import timedelta
        one_year_ago = datetime.now() - timedelta(days=365)
        past_investments_sum = db.query(func.sum(models.Ledger.amount)).filter(
            models.Ledger.user_id == user.id,
            models.Ledger.created_at >= one_year_ago,
            models.Ledger.transaction_type == "investment",
            models.Ledger.status.in_(["pending_settlement", "settled", "pending_payment"])
        ).scalar() or 0.0

        if not ComplianceService.check_investment_limit(user, investment_in.amount, past_investments_sum):
             raise HTTPException(status_code=403, detail="Investment exceeds SEC § 227.100 limits for non-accredited investors")
        is_compliant = True

    # Lane B: Reg D 506(b)
    elif campaign.regulation_type == "506_B":
        if not ComplianceService.check_reg_d_506b(user):
             raise HTTPException(status_code=403, detail="Reg D 506(b) Requirements Failed: User must be known >30 days and Self-Certified.")
        is_compliant = True

    # Lane C: Reg D 506(c)
    elif campaign.regulation_type == "506_C":
        if not ComplianceService.check_reg_d_506c(user):
             raise HTTPException(status_code=403, detail="Reg D 506(c) Requirements Failed: User must be Verified by Admin.")
        is_compliant = True

    else:
        # Default/Fallback (Treat as Reg CF or Fail)
        raise HTTPException(status_code=400, detail="Unknown Regulation Type")

    # --- THE TURNSTILE (Monetization) ---
    if is_compliant:
        from app.models.billing import BillingLog
        billing_log = BillingLog(
            user_id=user.id,
            transaction_id=f"val_{user.id}_{campaign.id}_{int(datetime.now().timestamp())}",
            description=f"Validation Check: {campaign.regulation_type}",
            fee_amount=2.00
        )
        db.add(billing_log)
        db.commit() # Commit the fee immediately
    
    # --- EXECUTION (Money Mover) ---
    try:
        from app.services.stripe_service import StripeService
        payment_intent = StripeService.create_payment_intent(
            amount=investment_in.amount,
            metadata={
                "user_id": user.id,
                "campaign_id": campaign.id,
                "transaction_type": "investment"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 4. Create Ledger Entry
    ledger_entry = models.Ledger(
        user_id=investment_in__user_id,
        campaign_id=investment_in.campaign_id,
        amount=investment_in.amount,
        transaction_type=investment_in.transaction_type,
        status="pending_payment", # Wait for webhook
        stripe_payment_intent_id=payment_intent.id
    )
    db.add(ledger_entry)
    db.commit()
    db.refresh(ledger_entry)

    # Attach client_secret for frontend (not saved in DB)
    ledger_entry.client_secret = payment_intent.client_secret
    
    # Send Email
    EmailService.send_email(
        to_email=user.email,
        subject="Investment Initiated",
        html_content=f"You have initiated an investment of ${investment_in.amount} in {campaign.name}."
    )

    return ledger_entry

@router.post("/investments/{investment_id}/cancel", response_model=schemas.Ledger)
def cancel_investment(
    investment_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Cancel investment (Checks 48-hour rule).
    """
    ledger_entry = db.query(models.Ledger).filter(models.Ledger.id == investment_id).first()
    if not ledger_entry:
        raise HTTPException(status_code=404, detail="Investment not found")
    
    if ledger_entry.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    campaign = db.query(models.Campaign).filter(models.Campaign.id == ledger_entry.campaign_id).first()
    
    # Compliance: 48-Hour Rule
    if not ComplianceService.check_cancellation_window(campaign.deadline):
        raise HTTPException(status_code=403, detail="Cancellation window closed (within 48 hours of deadline)")

    # Refund via Stripe
    if ledger_entry.stripe_payment_intent_id:
        try:
            from app.services.stripe_service import StripeService
            StripeService.refund_payment(ledger_entry.stripe_payment_intent_id)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Stripe Refund Failed: {str(e)}")

    ledger_entry.status = "cancelled"
    db.commit()
    db.refresh(ledger_entry)

    # Send Email
    EmailService.send_email(
        to_email=current_user.email,
        subject="Investment Cancelled",
        html_content=f"Your investment of ${ledger_entry.amount} has been successfully cancelled."
    )

    return ledger_entry

@router.post("/trade", response_model=schemas.Ledger)
def trade_secondary_market(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
    trade_in: schemas.LedgerCreate,
    original_transaction_date: datetime, # simplified for demo
) -> Any:
    """
    Secondary market trade (Checks Lockup).
    """
    # Compliance Check
    if not ComplianceService.check_lockup_period(original_transaction_date):
        raise HTTPException(status_code=403, detail="Asset is under 1-year lockup period (SEC Rule 501)")

    ledger_entry = models.Ledger(
        user_id=current_user.id,
        campaign_id=trade_in.campaign_id,
        amount=trade_in.amount,
        transaction_type=trade_in.transaction_type,
        status=trade_in.status,
    )
    db.add(ledger_entry)
    db.commit()
    db.refresh(ledger_entry)
    return ledger_entry

@router.get("/{user_id}", response_model=List[schemas.Ledger])
def read_transactions(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve user transactions.
    """
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view these transactions")
    
    transactions = db.query(models.Ledger).filter(models.Ledger.user_id == user_id).offset(skip).limit(limit).all()
    return transactions
