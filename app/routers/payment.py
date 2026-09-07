from datetime import datetime
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.schemas.payment import (
    PaymentInitializeRequest,
    PaymentInitializeResponse,
    PaymentVerifyRequest,
    PaymentVerifyResponse,
)
from app.services.paystack_service import (
    initialize_transaction,
    verify_transaction,
)

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post(
    "/initialize",
    response_model=PaymentInitializeResponse,
)
def initialize_payment(
    request: PaymentInitializeRequest,
    db: Session = Depends(get_db),
):
    plan = db.execute(
        select(Plan).where(Plan.id == request.plan_id)
    ).scalar_one_or_none()

    if plan is None:
        raise HTTPException(
            status_code=404,
            detail="Plan not found",
        )

    if plan.price_kobo == 0:
        raise HTTPException(
            status_code=400,
            detail="Free plans do not require payment",
        )

    try:
        transaction = initialize_transaction(
            email=request.email,
            amount=plan.price_kobo,
            plan_code=plan.paystack_plan_code,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Paystack payment initialization failed: {exc}",
        )

    subscription = Subscription(
        tenant_id=request.tenant_id,
        plan_id=plan.id,
        paystack_reference=transaction["reference"],
        status="pending",
    )

    db.add(subscription)
    db.commit()

    return PaymentInitializeResponse(
        authorization_url=transaction["authorization_url"],
        access_code=transaction["access_code"],
        reference=transaction["reference"],
    )

@router.post(
    "/verify",
    response_model=PaymentVerifyResponse,
)
def verify_payment(
    request: PaymentVerifyRequest,
    db: Session = Depends(get_db),
):
    subscription = db.execute(
        select(Subscription).where(
            Subscription.paystack_reference == request.reference
        )
    ).scalar_one_or_none()

    if subscription is None:
        raise HTTPException(
            status_code=404,
            detail="Subscription not found",
        )

    plan = db.execute(
        select(Plan).where(
            Plan.id == subscription.plan_id
        )
    ).scalar_one_or_none()

    if plan is None:
        raise HTTPException(
            status_code=404,
            detail="Plan not found",
        )
    if subscription.status == "active":
        return PaymentVerifyResponse(
            reference=request.reference,
            status="success",
            amount=plan.price_kobo,
            subscription_status=subscription.status,
        )

    try:
        transaction = verify_transaction(request.reference)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Paystack payment verification failed: {exc}",
        )

    if transaction["status"] != "success":
        raise HTTPException(
            status_code=400,
            detail="Payment was not successful",
        )

    if transaction["amount"] != plan.price_kobo:
        raise HTTPException(
            status_code=400,
            detail="Payment amount does not match plan price",
        )

    now = datetime.now()

    subscription.status = "active"
    subscription.current_period_start = now
    subscription.current_period_end = now + relativedelta(months=1)

    db.commit()
    db.refresh(subscription)

    return PaymentVerifyResponse(
        reference=transaction["reference"],
        status=transaction["status"],
        amount=transaction["amount"],
        subscription_status=subscription.status,
    )