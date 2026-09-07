from pydantic import BaseModel, EmailStr, Field


class PaymentInitializeRequest(BaseModel):
    tenant_id: int
    plan_id: int
    email: EmailStr


class PaymentInitializeResponse(BaseModel):
    authorization_url: str
    access_code: str
    reference: str


class PaymentVerifyRequest(BaseModel):
    reference: str


class PaymentVerifyResponse(BaseModel):
    reference: str
    status: str
    amount: int
    subscription_status: str