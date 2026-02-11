from celery import Celery
from app.core.config import settings

# For Windows compatibility we might need to use 'solo' pool or similar in worker command
# but the app config itself is standard.
# Ensure REDIS_URL is in settings or hardcode for now if missing.

celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# celery_app.conf.task_routes = {
#     "app.worker.settle_investment_task": "main-queue",
# }

# Fix circular import: Import worker tasks after app is initialized
celery_app.conf.imports = ["app.worker"]
