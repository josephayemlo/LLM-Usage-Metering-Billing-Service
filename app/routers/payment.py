from datetime import datetime
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.payment import Payment, PaymentStatus
from app.models.plan import Plan
from app.models.subscription import Subscription, SubscriptionStatus
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
    # 1. Check if this tenant already has a paid payment
    paid_payment = db.execute(
        select(Payment).where(
            Payment.tenant_id == request.tenant_id,
            Payment.status == PaymentStatus.PAID,
        )
    ).scalars().first()

    if paid_payment:
        return PaymentInitializeResponse(
            status="paid",
            authorization_url=None,
            access_code=None,
            reference=paid_payment.reference,
        )

    # 2. Check for an existing pending payment
    pending_payment = db.execute(
        select(Payment).where(
            Payment.tenant_id == request.tenant_id,
            Payment.status == PaymentStatus.PENDING,
        )
    ).scalars().first()

    if pending_payment:
        return PaymentInitializeResponse(
            status="pending",
            authorization_url=pending_payment.authorization_url,
            access_code=pending_payment.access_code,
            reference=pending_payment.reference,
        )

    # 3. Get the Pro plan
    pro_plan = db.execute(
        select(Plan).where(
            Plan.name == "Pro"
        )
    ).scalar_one_or_none()

    if pro_plan is None:
        raise HTTPException(
            status_code=404,
            detail="Pro plan not found",
        )

    # 4. Make sure Pro isn't free
    if pro_plan.price_kobo == 0:
        raise HTTPException(
            status_code=400,
            detail="Free plans do not require payment",
        )

    # 5. Initialize transaction with Paystack
    try:
        transaction = initialize_transaction(
            email=request.email,
            amount=pro_plan.price_kobo,
            plan_code=pro_plan.paystack_plan_code,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Paystack payment initialization failed: {exc}",
        )

    # 6. Save the payment as pending
    payment = Payment(
        tenant_id=request.tenant_id,
        plan_id=pro_plan.id,
        amount=pro_plan.price_kobo,
        reference=transaction["reference"],
        authorization_url=transaction["authorization_url"],
        access_code=transaction["access_code"],
        status=PaymentStatus.PENDING,
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    # 7. Return Paystack payment details
    return PaymentInitializeResponse(
        status="pending",
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
    payment = db.execute(
        select(Payment).where(
            Payment.reference == request.reference
        )
    ).scalar_one_or_none()

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    plan = db.execute(
        select(Plan).where(
            Plan.id == payment.plan_id
        )
    ).scalar_one_or_none()

    if plan is None:
        raise HTTPException(
            status_code=404,
            detail="Plan not found",
        )

    # Idempotency: don't process an already-paid payment again.
    if payment.status == PaymentStatus.PAID:
        subscription = db.execute(
            select(Subscription).where(
                Subscription.tenant_id == payment.tenant_id,
                Subscription.plan_id == payment.plan_id,
                Subscription.status == SubscriptionStatus.ACTIVE,
            )
        ).scalar_one_or_none()

        return PaymentVerifyResponse(
            reference=payment.reference,
            status="success",
            amount=payment.amount,
            subscription_status=(
                subscription.status
                if subscription
                else SubscriptionStatus.ACTIVE
            ),
        )

    try:
        transaction = verify_transaction(request.reference)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Paystack payment verification failed: {exc}",
        )

    if transaction["status"] != "success":
        payment.status = PaymentStatus.FAILED
        db.commit()

        raise HTTPException(
            status_code=400,
            detail="Payment was not successful",
        )

    if transaction["amount"] != payment.amount:
        raise HTTPException(
            status_code=400,
            detail="Payment amount does not match payment record",
        )

    now = datetime.now()

    payment.status = PaymentStatus.PAID

    subscription = db.execute(
        select(Subscription).where(
            Subscription.tenant_id == payment.tenant_id
        )
    ).scalar_one_or_none()

    if subscription is None:
        subscription = Subscription(
            tenant_id=payment.tenant_id,
            plan_id=payment.plan_id,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=now,
            current_period_end=now + relativedelta(months=1),
            paystack_reference=payment.reference,
        )

        db.add(subscription)

    else:
        subscription.plan_id = payment.plan_id
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.current_period_start = now
        subscription.current_period_end = now + relativedelta(months=1)
        subscription.paystack_reference = payment.reference

    db.commit()
    db.refresh(payment)
    db.refresh(subscription)

    return PaymentVerifyResponse(
        reference=payment.reference,
        status="success",
        amount=payment.amount,
        subscription_status=subscription.status,
    )