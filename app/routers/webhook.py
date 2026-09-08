import hashlib
import hmac
import json
import os
from datetime import datetime

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.payment import Payment, PaymentStatus
from app.models.payment_event import PaymentEvent
from app.models.subscription import Subscription, SubscriptionStatus


router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")


@router.post("/paystack")
async def paystack_webhook(
    request: Request,
    x_paystack_signature: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    # 1. Check Paystack signature
    if not x_paystack_signature:
        raise HTTPException(
            status_code=401,
            detail="Missing Paystack signature",
        )

    payload = await request.body()

    expected_signature = hmac.new(
        PAYSTACK_SECRET_KEY.encode(),
        payload,
        hashlib.sha512,
    ).hexdigest()

    if not hmac.compare_digest(
        expected_signature,
        x_paystack_signature,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid Paystack signature",
        )

    # 2. Parse webhook payload
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload",
        )

    event_type = data.get("event")

    # 3. Only process successful charges
    if event_type != "charge.success":
        return {"status": "ignored"}

    transaction = data.get("data", {})
    reference = transaction.get("reference")

    if not reference:
        raise HTTPException(
            status_code=400,
            detail="Missing transaction reference",
        )

    # 4. Check whether this event was already processed
    existing_event = db.execute(
        select(PaymentEvent).where(
            PaymentEvent.event_id == reference
        )
    ).scalar_one_or_none()

    if existing_event is not None:
        return {"status": "already_processed"}

    # 5. Find the actual payment
    payment = db.execute(
        select(Payment).where(
            Payment.reference == reference
        )
    ).scalar_one_or_none()

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    # 6. Idempotency at payment level
    if payment.status == PaymentStatus.PAID:
        return {"status": "already_processed"}

    # 7. Verify transaction status
    if transaction.get("status") != "success":
        return {"status": "ignored"}

    # 8. Verify amount against the payment record
    if transaction.get("amount") != payment.amount:
        raise HTTPException(
            status_code=400,
            detail="Payment amount does not match payment record",
        )

    # 9. Mark payment as paid
    payment.status = PaymentStatus.PAID

    # 10. Find the tenant's subscription
    subscription = db.execute(
        select(Subscription).where(
            Subscription.tenant_id == payment.tenant_id
        )
    ).scalar_one_or_none()

    now = datetime.now()

    if subscription is None:
        # Create subscription if one doesn't exist
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
        # Upgrade existing subscription
        subscription.plan_id = payment.plan_id
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.current_period_start = now
        subscription.current_period_end = now + relativedelta(months=1)
        subscription.paystack_reference = payment.reference

    # 11. Record webhook event
    payment_event = PaymentEvent(
        event_id=reference,
        event_type=event_type,
        reference=reference,
    )

    db.add(payment_event)

    # 12. Commit everything together
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return {"status": "already_processed"}

    return {"status": "processed"}