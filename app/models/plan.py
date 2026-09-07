from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

#The Plan model represents a subscription plan in the system.
class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    price_kobo: Mapped[int] = mapped_column( Integer,nullable=False,)
    billing_interval: Mapped[str] = mapped_column(String(20),nullable=False,default="monthly",)
    paystack_plan_code: Mapped[str | None] = mapped_column(String(255),nullable=True,unique=True,)
    api_call_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    ai_token_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    ai_budget_micro_units: Mapped[int] = mapped_column(default=0,nullable=False,)
    created_at: Mapped[datetime] = mapped_column( DateTime, default=datetime.now, nullable=False)