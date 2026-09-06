from pydantic import BaseModel

class SubscriptionCreate(BaseModel):
    tenant_id: int
    plan_id: int
    status: str


class SubscriptionResponse(BaseModel):
    id: int
    tenant_id: int
    plan_id: int
    status: str

    model_config = {
        "from_attributes": True
    }