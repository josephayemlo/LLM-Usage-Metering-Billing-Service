from pydantic import BaseModel, Field
from enum import Enum



# UsageType enum to define the allowed usage types
class UsageType(str, Enum):
    API_CALL = "api_call"
    AI_TOKEN = "ai_token"


"""
This helps us define the data that enters and leaves the API.
Not all data in the Tenant model is needed in the API
For example, the Tenant model has a created_at field that is automatically set by the database, 
but we don't need to send that to the API. 
"""
class TenantCreate(BaseModel):
    name: str


"""
This helps us define the data to be sent back to the API when a tenant is created or retrieved.
We don't want to send all the data in the Tenant model to the API,
so we define a separate schema for the response.
We dontt need to send the created_at field to the API, so we don't include it in the response schema.
But an id is needed to identify the tenant, so we include it in the response schema.
This is what the user will receive as a response after creating a new tenant.
"""
class TenantResponse(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True
    }


# Subscription schemas
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

# Usage schemas
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

