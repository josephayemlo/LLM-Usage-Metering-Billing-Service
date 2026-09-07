import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base
from app.dependencies import get_db
from app.main import app
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.models.tenant import Tenant


@pytest.fixture
def db():
    engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
    Base.metadata.create_all(engine)

    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()

    tenant = Tenant(name="Webhook Test Tenant")

    plan = Plan(
        name="Webhook Test Plan",
        api_call_limit=1000,
        ai_token_limit=100000,
        price_kobo=500000,
    )

    session.add_all([tenant, plan])
    session.commit()

    subscription = Subscription(
        tenant_id=tenant.id,
        plan_id=plan.id,
        status="pending",
        paystack_reference="TEST-REFERENCE-123",
    )

    session.add(subscription)
    session.commit()

    yield session

    session.close()


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)

    app.dependency_overrides.clear()


def make_signature(payload: bytes) -> str:
    secret = os.getenv("PAYSTACK_SECRET_KEY")

    return hmac.new(
        secret.encode(),
        payload,
        hashlib.sha512,
    ).hexdigest()


def test_invalid_signature_is_rejected(client):
    payload = json.dumps({
        "event": "charge.success",
        "data": {
            "reference": "TEST-REFERENCE-123",
            "status": "success",
            "amount": 500000,
        },
    }).encode()

    response = client.post(
        "/webhooks/paystack",
        content=payload,
        headers={
            "x-paystack-signature": "invalid-signature",
        },
    )

    assert response.status_code == 401


def test_valid_webhook_activates_subscription(client, db):
    payload = json.dumps({
        "event": "charge.success",
        "data": {
            "reference": "TEST-REFERENCE-123",
            "status": "success",
            "amount": 500000,
        },
    }).encode()

    response = client.post(
        "/webhooks/paystack",
        content=payload,
        headers={
            "x-paystack-signature": make_signature(payload),
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "processed"

    subscription = db.query(Subscription).first()

    assert subscription.status == "active"
    assert subscription.current_period_start is not None
    assert subscription.current_period_end is not None


def test_duplicate_webhook_is_not_processed_twice(client, db):
    payload = json.dumps({
        "event": "charge.success",
        "data": {
            "reference": "TEST-REFERENCE-123",
            "status": "success",
            "amount": 500000,
        },
    }).encode()

    signature = make_signature(payload)

    first_response = client.post(
        "/webhooks/paystack",
        content=payload,
        headers={"x-paystack-signature": signature},
    )

    second_response = client.post(
        "/webhooks/paystack",
        content=payload,
        headers={"x-paystack-signature": signature},
    )

    assert first_response.json()["status"] == "processed"
    assert second_response.json()["status"] == "already_processed"

    from app.models.payment_event import PaymentEvent

    events = db.query(PaymentEvent).all()

    assert len(events) == 1