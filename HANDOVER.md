# Reg-Router Project Handover 🚀

**Date:** 2026-02-09
**Current Status:** Phase 3 (Production Hardening) - Dockerization In Progress

## 1. What We Have Built (Completed) ✅
We have a functional **FastAPI** application for investment regulation compliance.
*   **Core API**: Users, Campaigns, Ledger endpoints (`app/api/v1/`).
*   **Database**: SQLite (`sql_app.db`) with SQLAlchemy ORM (`app/models/`).
*   **Compliance Logic**: KYC checks, Lockup periods, Escrow thresholds (`app/services/compliance.py`).
*   **Async Task Queue**:
    *   **Redis** as the message broker.
    *   **Celery** worker (`app/worker.py`) handling background investment settlement.
*   **Authentication**:
    *   **JWT** (JSON Web Tokens) for secure access.
    *   **Argon2** password hashing.
    *   Login endpoint: `/api/v1/login/access-token`.

## 2. Work In Progress (Dockerization) 🚧
We just created the containerization files to make deployment easier.
*   **`Dockerfile`**: Created. Defines the Python environment.
*   **`docker-compose.yml`**: Created. Orchestrates `web` (API), `worker`, and `redis`.
*   **`app/core/config.py`**: Updated to read config from env vars (Docker-ready).
*   **`app/db/session.py`**: Updated to use `DATABASE_URL` from settings.

**Immediate Next Step:**
*   Run `docker-compose up --build` on the new machine to verify the container setup works.

## 3. Future Roadmap (To-Do) Qt
*   [ ] **Verify Docker**: Confirm the app runs smoothly in containers.
*   [ ] **Switch to PostgreSQL**: Update `docker-compose.yml` to use a Postgres image instead of SQLite file.
*   [ ] **Error Monitoring**: Add Sentry.
*   [ ] **CI/CD**: Set up GitHub Actions.

## 4. Setup Instructions for New Machine 💻

### Prerequisites
1.  **Install Docker Desktop**: [Download Here](https://www.docker.com/products/docker-desktop).
2.  **Install Python 3.11+** (Optional if using Docker, but good for local dev).
3.  **Git Clone** this repository.

### Option A: Run via Docker (Recommended)
This is what we were just working on. It should work out of the box.
```bash
# 1. Build and Start Services
docker-compose up --build

# 2. Access API
http://localhost:8000/docs
```

### Option B: Run Locally (Old Way)
If you want to run without Docker for debugging:
1.  **Install Redis**: Must be running locally on port 6379.
2.  **Install Requirements**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run with Script**:
    ```bash
    ./run_dev.bat
    ```

## 5. Key Credentials (Development)
*   **Test User**: `auth_user@example.com` / `SecurePassword123!`
*   **API Auth**: Use the "Authorize" button in Swagger UI.

## 6. Known "Gotchas"
*   **Database Reset**: If you switch between Docker and Local, or change the User model, you might need to delete `sql_app.db` to let it recreate.
*   **Windows vs Linux**: The `run_dev.bat` is for Windows. Docker hides these differences.
