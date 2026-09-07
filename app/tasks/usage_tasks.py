import logging

from celery import Task
from sqlalchemy import func, select

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.subscription import Subscription
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
        subscription = db.execute(
            select(Subscription).where(
                Subscription.tenant_id == tenant_id,
                Subscription.status == "active",
            )
        ).scalar_one_or_none()

        if subscription is None:
            raise ValueError("Active subscription not found")

        api_calls = db.query(
            func.coalesce(
                func.sum(UsageEvent.quantity),
                0,
            )
        ).filter(
            UsageEvent.tenant_id == tenant_id,
            UsageEvent.usage_type == "api_call",
            UsageEvent.created_at >= subscription.current_period_start,
            UsageEvent.created_at < subscription.current_period_end,
        ).scalar()

        ai_tokens = db.query(
            func.coalesce(
                func.sum(UsageEvent.quantity),
                0,
            )
        ).filter(
            UsageEvent.tenant_id == tenant_id,
            UsageEvent.usage_type == "ai_token",
            UsageEvent.created_at >= subscription.current_period_start,
            UsageEvent.created_at < subscription.current_period_end,
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