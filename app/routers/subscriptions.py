from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.subscription import  SubscriptionResponse
from app.services.subscription_service import (
    get_subscription, 
    get_all_subscriptions
)

router = APIRouter(
    prefix="/subscriptions",
    tags=["Subscriptions"],
)

# Endpoint to retrieve an existing subscription by its ID from the database.
@router.get("/{subscription_id}", response_model=SubscriptionResponse)
def get_existing_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
):
    subscription = get_subscription(db, subscription_id)

    if subscription is None:
        raise HTTPException(
            status_code=404,
            detail="Subscription not found",
        )

    return subscription
# Endpoint to retrieve all subscriptions from the database.
@router.get("/", response_model=list[SubscriptionResponse])
def get_subscriptions(
    db: Session = Depends(get_db),
):
    return get_all_subscriptions(db)