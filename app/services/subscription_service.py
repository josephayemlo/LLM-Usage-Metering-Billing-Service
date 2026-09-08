from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.subscription import Subscription


# Retrieves a subscription by its ID from the database.
def get_subscription(
    db: Session,
    subscription_id: int,
) -> Subscription | None:
    return db.execute(
        select(Subscription).where(
            Subscription.id == subscription_id
        )
    ).scalar_one_or_none()
# Retrieves all subscriptions from the database.
def get_all_subscriptions(db: Session) -> list[Subscription]:
    return db.execute(
        select(Subscription)
    ).scalars().all()