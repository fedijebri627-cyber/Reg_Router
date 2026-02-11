
from fastapi import APIRouter, Header, HTTPException, Request, Depends
from sqlalchemy.orm import Session
from app import models
from app.api import deps
from app.core import config
from app.services.stripe_service import StripeService

router = APIRouter()

@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    db: Session = Depends(deps.get_db),
):
    payload = await request.body()
    
    try:
        event = StripeService.construct_event(
            payload, stripe_signature, config.settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid Stripe Signature")

    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        # Find ledger entry by pi_id
        ledger_entry = db.query(models.Ledger).filter(
            models.Ledger.stripe_payment_intent_id == payment_intent["id"]
        ).first()
        if ledger_entry:
            ledger_entry.status = "settled"
            db.commit()

    elif event["type"] == "payment_intent.payment_failed":
        payment_intent = event["data"]["object"]
        ledger_entry = db.query(models.Ledger).filter(
             models.Ledger.stripe_payment_intent_id == payment_intent["id"]
        ).first()
        if ledger_entry:
             ledger_entry.status = "failed"
             db.commit()

    return {"status": "success"}
