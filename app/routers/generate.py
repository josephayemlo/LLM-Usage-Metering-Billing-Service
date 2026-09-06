from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.generate import GenerateRequest, GenerateResponse
from app.services.usage_service import record_usage

router = APIRouter(prefix="/generate", tags=["Generate"])


@router.post("/", response_model=GenerateResponse)
def generate(
    request: GenerateRequest,
    idempotency_key: str = Header(...),
    db: Session = Depends(get_db),
):
    input_tokens = len(request.prompt.split())
    output_tokens = 20
    total_tokens = input_tokens + output_tokens

    record_usage(
        db=db,
        tenant_id=request.tenant_id,
        usage_type="ai_token",
        quantity=total_tokens,
        idempotency_key=idempotency_key,
    )

    return GenerateResponse(
        tenant_id=request.tenant_id,
        output="This is a simulated AI response.",
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
    )