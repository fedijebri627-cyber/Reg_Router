import time
import logging
from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.ledger import Ledger

@celery_app.task(acks_late=True)
def settle_investment_task(ledger_id: int):
    db = SessionLocal()
    try:
        # Simulate bank transfer delay
        time.sleep(10)
        
        ledger_entry = db.query(Ledger).filter(Ledger.id == ledger_id).first()
        if ledger_entry and ledger_entry.status == "pending_settlement":
            ledger_entry.status = "settled"
            db.commit()
            logging.info(f"Investment {ledger_id} settled successfully.")
        else:
            logging.warning(f"Investment {ledger_id} not found or already processed.")
    except Exception as e:
        logging.error(f"Error settling investment {ledger_id}: {e}")
    finally:
        db.close()
