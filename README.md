# Reg-Router: The Compliance API

## Overview
Reg-Router is a "Compliance-as-Code" API for US Equity Crowdfunding (Reg CF). It acts as a gatekeeper between Funding Portals and Stripe, enforcing SEC rules like § 227.303 (Escrow) and § 227.501 (Secondary Market Lockup).

## Technology Stack
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Database**: PostgreSQL (managed via SQLAlchemy and Alembic)
- **Task Queue**: Redis/Celery (Coming in Phase 2)

## Setup
1. **Prerequisites**: Python 3.11+, PostgreSQL installed.
2. **Installation**:
   ```bash
   setup_project.bat
   ```
   Or manually:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Environment**:
   Copy `.env.example` to `.env` and configure your database URL.
   ```bash
   copy .env.example .env
   ```
4. **Run**:
   ```bash
   uvicorn app.main:app --reload
   ```
   Visit `http://localhost:8000/docs` for the Swagger UI.

## Phase 1: The Auditor
- Database Schema: Users, Campaigns, Ledger
- Compliance Service: Validates KYC, Lockup periods, and Escrow thresholds.
