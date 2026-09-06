from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    tenant_id: int
    prompt: str = Field(min_length=1)


class GenerateResponse(BaseModel):
    tenant_id: int
    output: str
    input_tokens: int
    output_tokens: int
    total_tokens: int