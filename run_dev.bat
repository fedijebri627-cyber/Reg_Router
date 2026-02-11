@echo off
echo Starting Reg-Router Development Environment...

:: Start Celery Worker in a new window
start "Reg-Router Worker" cmd /k "celery -A app.core.celery_app worker --loglevel=info --pool=solo"

:: Start FastAPI App in a new window
start "Reg-Router API" cmd /k "uvicorn app.main:app --reload"

echo Services started!
echo API: http://localhost:8000/docs
