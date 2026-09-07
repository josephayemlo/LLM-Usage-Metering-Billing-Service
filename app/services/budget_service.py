from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.plan import Plan
from app.models.subscription import Subscription
from app.models.usage_event import UsageEvent


class AIBudgetExceededError(Exception):
    pass


def check_ai_budget(
    db: Session,
    tenant_id: int,
    cost_micro_units: int,
) -> bool:
    subscription = db.execute(
        select(Subscription).where(
            Subscription.tenant_id == tenant_id,
            Subscription.status == "active",
        )
    ).scalar_one_or_none()

    if subscription is None:
        return False

    plan = db.execute(
        select(Plan).where(
            Plan.id == subscription.plan_id
        )
    ).scalar_one_or_none()

    if plan is None:
        return False

    current_cost = db.execute(
        select(
            func.coalesce(
                func.sum(UsageEvent.cost_micro_units),
                0,
            )
        ).where(
            UsageEvent.tenant_id == tenant_id,
            UsageEvent.usage_type == "ai_token",
            UsageEvent.created_at >= subscription.current_period_start,
            UsageEvent.created_at < subscription.current_period_end,
        )
    ).scalar_one()

    return current_cost + cost_micro_units <= plan.ai_budget_micro_units