import hashlib
import hmac
import json
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.payment_event import PaymentEvent
from app.models.plan import Plan
from app.models.subscription import Subscription

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")


@router.post("/paystack")
async def paystack_webhook(
    request: Request,
    x_paystack_signature: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
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

    data = json.loads(payload)

    event_type = data.get("event")

    if event_type != "charge.success":
        return {"status": "ignored"}

    transaction = data.get("data", {})
    reference = transaction.get("reference")

    if not reference:
        raise HTTPException(
            status_code=400,
            detail="Missing transaction reference",
        )

    existing_event = db.execute(
        select(PaymentEvent).where(
            PaymentEvent.event_id == reference
        )
    ).scalar_one_or_none()

    if existing_event is not None:
        return {"status": "already_processed"}

    subscription = db.execute(
        select(Subscription).where(
            Subscription.paystack_reference == reference
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

    if transaction.get("status") != "success":
        return {"status": "ignored"}

    if transaction.get("amount") != plan.price_kobo:
        raise HTTPException(
            status_code=400,
            detail="Payment amount does not match plan price",
        )

    payment_event = PaymentEvent(
        event_id=reference,
        event_type=event_type,
        reference=reference,
    )

    db.add(payment_event)

    now = datetime.now()

    subscription.status = "active"
    subscription.current_period_start = now
    subscription.current_period_end = now + relativedelta(months=1)

    db.commit()

    return {"status": "processed"}