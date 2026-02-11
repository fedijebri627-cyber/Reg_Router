from datetime import datetime, timedelta
from app.schemas.user import User
from app.schemas.campaign import Campaign

class ComplianceService:
    @staticmethod
    def check_kyc(user: User) -> bool:
        """
        Validates if a user is KYC verified.
        """
        return user.kyc_status == "verified"

    @staticmethod
    def check_lockup_period(transaction_date: datetime) -> bool:
        """
        Enforces the 1-year lockup rule for secondary sales (SEC § 227.501).
        Returns True if the lockup period has passed (trade allowed), False otherwise.
        """
        one_year_later = transaction_date.replace(year=transaction_date.year + 1)
        return datetime.now(transaction_date.tzinfo) >= one_year_later

    @staticmethod
    def check_escrow_threshold(campaign: Campaign, current_pledged: float) -> bool:
        """
        Checks if a campaign has met its target amount (SEC § 227.303).
        """
        return current_pledged >= campaign.target_amount

    @staticmethod
    def check_investment_limit(user: User, amount: float, past_12mo_investments: float) -> bool:
        """
        Enforces SEC § 227.100 investment limits.
        Non-accredited investors: Cap at greater of $2,500 or 5% of annual income/net worth (if <$124k).
        Accredited investors: No limit (in this simplified version, though strictly it's different).
        """
        if user.is_accredited:
            return True

        # Simplified Logic for Non-Accredited
        # Limit is greater of $2,500 or 5% of lesser of annual_income or net_worth
        # If income/net_worth are missing, default to stricter $2,500 limit
        
        income = user.annual_income or 0
        net_worth = user.net_worth or 0
        
        limit_base = min(income, net_worth)
        calculated_limit = max(2500, limit_base * 0.05)
        
        return (past_12mo_investments + amount) <= calculated_limit

    @staticmethod
    def check_reg_d_506b(user: User) -> bool:
        """
        Lane B: Reg D Rule 506(b) (The "Private" Lane)
        Logic 1: Cool-Off (User > 30 days old)
        Logic 2: Accredited (Self-Certified)
        """
        # 1. Cool-off Check
        if not user.created_at:
             return False # Should not happen if schema is enforcing
        
        thirty_days_ago = datetime.now(user.created_at.tzinfo) - timedelta(days=30)
        if user.created_at > thirty_days_ago:
            return False # User is too new

        # 2. Accreditation Check (Honor System)
        if user.accreditation_status != "SELF_CERTIFIED" and user.accreditation_status != "VERIFIED_DOCS":
            return False

        return True

    @staticmethod
    def check_reg_d_506c(user: User) -> bool:
        """
        Lane C: Reg D Rule 506(c) (The "Public" Lane)
        Logic 1: Proof (Verified Docs)
        Logic 2: Expiry Check (Within 90 days)
        """
        # 1. Verification Check
        if user.accreditation_status != "VERIFIED_DOCS":
            return False

        # 2. Expiry Check
        if not user.accreditation_expiry:
            return False
        
        # Ensure aware comparison
        expiry = user.accreditation_expiry
        if expiry.tzinfo is None:
             expiry = expiry.replace(tzinfo=datetime.now().tzinfo)

        if expiry < datetime.now(expiry.tzinfo):
            return False # Verification expired

        return True

    @staticmethod
    def check_cancellation_window(campaign_deadline: datetime) -> bool:
        """
        Enforces SEC § 227.304 cancellation rights.
        Investors can cancel up to 48 hours before the deadline.
        """
        time_until_deadline = campaign_deadline - datetime.now(campaign_deadline.tzinfo)
        return time_until_deadline > timedelta(hours=48)
