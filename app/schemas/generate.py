from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    tenant_id: int
    prompt: str = Field(min_length=1)
    cached_input_tokens: int = Field(default=0, ge=0)
    reasoning_tokens: int = Field(default=0, ge=0)


class GenerateResponse(BaseModel):
    tenant_id: int
    output: str
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    reasoning_tokens: int
    cost_micro_units: int
    total_tokens: int