from sqlalchemy.orm import Session

from app.models.subscription import Subscription
from app.models.plan import Plan
from app.services.usage_service import get_usage_total


class QuotaExceededError(Exception):
    pass


def check_quota(
    db: Session,
    tenant_id: int,
    usage_type: str,
    quantity: int,
) -> bool:
    subscription = db.query(Subscription).filter(
        Subscription.tenant_id == tenant_id
    ).first()

    if subscription is None:
        return False

    plan = db.query(Plan).filter(
        Plan.id == subscription.plan_id
    ).first()

    if plan is None:
        return False

    current_usage = get_usage_total(
        db,
        tenant_id,
        usage_type,
    )

    if usage_type == "api_call":
        limit = plan.api_call_limit
    elif usage_type == "ai_token":
        limit = plan.ai_token_limit
    else:
        return False

    return current_usage + quantity <= limit 
# The return statment:
# Checks if the current usage plus the requested quantity exceeds the limit. 
# If it does, return False (quota exceeded). Otherwise, return True (quota available).
