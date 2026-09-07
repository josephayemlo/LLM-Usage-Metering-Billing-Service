import logging

from celery import Task
from sqlalchemy import func

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.usage_event import UsageEvent

logger = logging.getLogger(__name__)


class RetryableTask(Task):
    autoretry_for = (Exception,)
    retry_backoff = True
    retry_kwargs = {"max_retries": 3}

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.critical(
            "ALERT: background task permanently failed. "
            "task_id=%s error=%s",
            task_id,
            exc,
        )


@celery_app.task(
    bind=True,
    base=RetryableTask,
)

def process_usage_summary(self, tenant_id: int):
    db = SessionLocal()

    try:
        api_calls = db.query(
            func.coalesce(
                func.sum(UsageEvent.quantity),
                0,
            )
        ).filter(
            UsageEvent.tenant_id == tenant_id,
            UsageEvent.usage_type == "api_call",
        ).scalar()

        ai_tokens = db.query(
            func.coalesce(
                func.sum(UsageEvent.quantity),
                0,
            )
        ).filter(
            UsageEvent.tenant_id == tenant_id,
            UsageEvent.usage_type == "ai_token",
        ).scalar()

        logger.info(
            "Usage summary for tenant %s: "
            "api_calls=%s, ai_tokens=%s",
            tenant_id,
            api_calls,
            ai_tokens,
        )

        return {
            "tenant_id": tenant_id,
            "api_calls": api_calls,
            "ai_tokens": ai_tokens,
            "status": "completed",
        }

    finally:
        db.close()