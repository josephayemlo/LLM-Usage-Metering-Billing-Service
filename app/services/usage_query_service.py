from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.usage_event import UsageEvent

# The get_usage_total function calculates the total quantity of a specific usage type for a given tenant.
def get_usage_total(
    db: Session,
    tenant_id: int,
    usage_type: str,
) -> int:
    total = db.execute(
        select(func.coalesce(func.sum(UsageEvent.quantity), 0))
        .where(
            UsageEvent.tenant_id == tenant_id,
            UsageEvent.usage_type == usage_type,
        )
    ).scalar_one()

    return total