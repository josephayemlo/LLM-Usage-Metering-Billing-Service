from pydantic import BaseModel
from app.models.subscription import SubscriptionStatus


class SubscriptionResponse(BaseModel):
    id: int
    tenant_id: int
    plan_id: int
    status: SubscriptionStatus
    paystack_reference: str | None

    model_config = {
        "from_attributes": True
    }