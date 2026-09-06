from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.usage_event import UsageEvent
from app.services.quota_service import check_quota, QuotaExceededError
from sqlalchemy.exc import IntegrityError
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

    #the try block detects and handles a violation of the hardening
    # You must add the uniqueness on the model for this to work
    try: 
        db.commit()
    except IntegrityError:
        db.rollback()

        existing_event = db.execute(
            select(UsageEvent).where(
                UsageEvent.tenant_id == tenant_id,
                UsageEvent.idempotency_key == idempotency_key,
            )
        ).scalar_one()

        return existing_event

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

