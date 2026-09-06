from pydantic import BaseModel, Field
from enum import Enum


class UsageType(str, Enum):
    API_CALL = "api_call"
    AI_TOKEN = "ai_token"


class UsageCreate(BaseModel):
    tenant_id: int
    usage_type: UsageType
    quantity: int = Field(gt=0) # The quantity must be greater than 0 to ensure that we don't record negative or zero usage events.


class UsageResponse(BaseModel):
    id: int
    tenant_id: int
    usage_type: UsageType
    quantity: int
    idempotency_key: str

    model_config = {
        "from_attributes": True
    }