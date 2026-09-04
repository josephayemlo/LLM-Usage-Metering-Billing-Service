from pydantic import BaseModel


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