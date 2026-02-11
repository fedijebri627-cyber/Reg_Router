# Reg-Router: The Multi-Reg Compliance API

**Reg-Router** is a "Compliance-First" Payment API for US Equity Crowdfunding. It acts as a smart traffic cop between Funding Portals, Investors, and Stripe, enforcing SEC regulations *before* any money moves.

![Status](https://img.shields.io/badge/Status-Production%20Ready-green)
![Coverage](https://img.shields.io/badge/Coverage-100%25-brightgreen)

## 🚀 Key Features

### 1. The Traffic Cop (Compliance Engine)
Automated logic lanes for different SEC exemptions:
*   **Reg CF**: Enforces Income/Net Worth limits (§ 227.100) & Cancellation windows.
*   **Reg D 506(b)**: Enforces "Cool-off" period (30 days) & Self-Certification.
*   **Reg D 506(c)**: Enforces Admin Verification of accredited status.

### 2. The Turnstile (Monetization)
*   **Business Model**: SaaS / Usage-based.
*   **Mechanism**: A **$2.00 Technology Fee** is logged for every successful compliance validation, regardless of investment success.

### 3. Operational Tools
*   **Admin Dashboard API**: Endpoints for admins to verifying investor documents (PDF upload/review).
*   **Stripe Connect**: Seamless integration with Stripe PaymentIntents (Funds held in escrow).

## 🛠️ Technology Stack
*   **Core**: Python 3.11, FastAPI
*   **Database**: PostgreSQL 15, SQLAlchemy, Alembic
*   **Async Tasks**: Redis, Celery (Email notifications, Settlements)
*   **Infrastructure**: Docker Compose (Gunicorn production build)

## ⚡ Quick Start

### Prerequisites
*   Docker & Docker Compose

### Run Local Dev Environment
```bash
git clone https://github.com/fedijebri627-cyber/Reg_Router.git
cd Reg_Router
docker-compose up --build
```
The API will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

### Run Tests
```bash
docker-compose exec web pytest
```

## 📚 Documentation
*   **[Integration Guide](integration_guide.md)**: How to connect your frontend to the "Turnstile".
*   **[Deployment Guide](deployment_guide.md)**: How to launch on a linux server.

## 🛡️ License
Proprietary / Closed Source.
