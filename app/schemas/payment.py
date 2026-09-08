from pydantic import BaseModel, EmailStr, Field


class PaymentInitializeRequest(BaseModel):
    tenant_id: int
    email: EmailStr


class PaymentInitializeResponse(BaseModel):
    status: str
    authorization_url: str | None = None
    access_code: str | None = None
    reference: str


class PaymentVerifyRequest(BaseModel):
    reference: str


class PaymentVerifyResponse(BaseModel):
    reference: str
    status: str
    amount: int
    subscription_status: str