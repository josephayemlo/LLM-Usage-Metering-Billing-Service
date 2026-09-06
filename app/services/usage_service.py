from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.usage_event import UsageEvent
from app.services.quota_service import check_quota, QuotaExceededError
"""
This function records the a new usage for a tenant, but it first checks if the request
has already been processed using the idempotency key to avoid duplicates. If it has not,
it checks the tenant's quota before creating and saving the usage event.
The idempontency check must be done before the quota check.
"""

def record_usage(
    db: Session,
    tenant_id: int,
    usage_type: str,
    quantity: int,
    idempotency_key: str,
) -> UsageEvent:
    # Check if a usage event with the same tenant_id and idempotency_key already exists in the database.
    #This helps avoid duplicate records for the same usage event.
    existing_event = db.execute(
        select(UsageEvent).where(
            UsageEvent.tenant_id == tenant_id,
            UsageEvent.idempotency_key == idempotency_key,
        )
    ).scalar_one_or_none()

    if existing_event is not None:
        return existing_event
    allowed = check_quota(
        db=db,
        tenant_id=tenant_id,
        usage_type=usage_type,
        quantity=quantity,
    )

    if not allowed:
        raise QuotaExceededError("usage quota exceeded")

    usage_event = UsageEvent(
        tenant_id=tenant_id,
        usage_type=usage_type,
        quantity=quantity,
        idempotency_key=idempotency_key,
    )

    db.add(usage_event)
    db.commit()
    db.refresh(usage_event)

    return usage_event

# The get_usage_event function retrieves a specific usage event from the database based on its ID.
def get_usage_event(
    db: Session,
    usage_event_id: int,
) -> UsageEvent | None:
    return db.execute(
        select(UsageEvent).where(
            UsageEvent.id == usage_event_id
        )
    ).scalar_one_or_none()

# The get_tenant_usage function retrieves all usage events for a specific tenant from the database.
def get_tenant_usage(
    db: Session,
    tenant_id: int,
) -> list[UsageEvent]:
    return db.execute(
        select(UsageEvent)
        .where(UsageEvent.tenant_id == tenant_id)
        .order_by(UsageEvent.created_at)
    ).scalars().all()

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