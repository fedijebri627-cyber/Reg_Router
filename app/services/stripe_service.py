
import stripe
from app.core import config
from app.core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeService:
    @staticmethod
    def create_payment_intent(amount: float, currency: str = "usd", metadata: dict = None, transfer_group: str = None) -> stripe.PaymentIntent:
        """
        Creates a PaymentIntent for an investment.
        Amount is in cents.
        """
        try:
            return stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency=currency,
                metadata=metadata or {},
                transfer_group=transfer_group,
                capture_method="manual",  # Hold funds in escrow
            )
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe Error: {str(e)}")

    @staticmethod
    def refund_payment(payment_intent_id: str) -> stripe.Refund:
        """
        Refunds a payment intent.
        """
        try:
            return stripe.Refund.create(payment_intent=payment_intent_id)
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe Error: {str(e)}")

    @staticmethod
    def construct_event(payload: bytes, sig_header: str, secret: str):
        """
        Verifies and reconstructs a webhook event.
        """
        return stripe.Webhook.construct_event(
            payload, sig_header, secret
        )
