from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas import UsageCreate, UsageResponse, UsageType
from app.services.usage_service import (
    record_usage,
    get_usage_event,
    get_tenant_usage,
)
from app.services.quota_service import check_quota, QuotaExceededError
from app.services.usage_query_service import get_usage_total




router = APIRouter(
    prefix="/usage",
    tags=["Usage"],
)



# The create_usage_event endpoint now checks the quota before recording the usage event.
@router.post("/", response_model=UsageResponse)
def create_usage_event(
    usage: UsageCreate,
    idempotency_key: str = Header(...),
    db: Session = Depends(get_db),
):
    try:
        return record_usage(
            db=db,
            tenant_id=usage.tenant_id,
            usage_type=usage.usage_type.value,
            quantity=usage.quantity,
            idempotency_key=idempotency_key,
        )
    except QuotaExceededError as exc:
        raise HTTPException(
            status_code=429,
            detail=str(exc),
        )



@router.get("/tenant/{tenant_id}", response_model=list[UsageResponse])
def get_usage_for_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
):
    return get_tenant_usage(db, tenant_id)

@router.get("/{usage_event_id}", response_model=UsageResponse)
def get_existing_usage_event(
    usage_event_id: int,
    db: Session = Depends(get_db),
):
    usage_event = get_usage_event(db, usage_event_id)

    if usage_event is None:
        raise HTTPException(
            status_code=404,
            detail="Usage event not found",
        )

    return usage_event



@router.get("/tenant/{tenant_id}/total")
def get_usage_total_for_tenant(
    tenant_id: int,
    usage_type: UsageType,
    db: Session = Depends(get_db),
):
    total = get_usage_total(
        db,
        tenant_id,
        usage_type.value,
    )

    return {
        "tenant_id": tenant_id,
        "usage_type": usage_type.value,
        "total": total,
    }

