from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from enum import Enum
from sqlalchemy import Enum as SQLEnum
from app.database import Base

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    PENDING = "pending"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

#The Subscription model represents a subscription for a specific tenant in the system.
class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=False,
    )

    plan_id: Mapped[int] = mapped_column(
        ForeignKey("plans.id"),
        nullable=False,
    )

    paystack_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
    )

    status: Mapped[SubscriptionStatus] = mapped_column(
    SQLEnum(SubscriptionStatus),
    nullable=False
    )

    current_period_start: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )