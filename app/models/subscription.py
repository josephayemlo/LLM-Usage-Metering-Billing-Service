from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id"), nullable=False
    )

    plan_id: Mapped[int] = mapped_column(
        ForeignKey("plans.id"), nullable=False
    )

    stripe_customer_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )

    stripe_subscription_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(50), nullable=False
    )

    current_period_start: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )