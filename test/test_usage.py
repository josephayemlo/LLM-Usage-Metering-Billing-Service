import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.tenant import Tenant
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.services.usage_service import record_usage
from app.services.quota_service import QuotaExceededError


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()

    tenant = Tenant(name="Test Tenant")
    plan = Plan(
        name="Test Plan",
        api_call_limit=1000,
        ai_token_limit=100,
    )

    session.add_all([tenant, plan])
    session.commit()

    subscription = Subscription(
        tenant_id=tenant.id,
        plan_id=plan.id,
        status="active",
    )

    session.add(subscription)
    session.commit()

    yield session

    session.close()


def test_idempotency_returns_existing_event(db):
    first = record_usage(
        db=db,
        tenant_id=1,
        usage_type="ai_token",
        quantity=20,
        idempotency_key="test-key",
    )

    second = record_usage(
        db=db,
        tenant_id=1,
        usage_type="ai_token",
        quantity=20,
        idempotency_key="test-key",
    )

    assert first.id == second.id

    events = db.query(
        __import__(
            "app.models.usage_event",
            fromlist=["UsageEvent"],
        ).UsageEvent
    ).all()

    assert len(events) == 1


def test_quota_boundary(db):
    record_usage(
        db=db,
        tenant_id=1,
        usage_type="ai_token",
        quantity=100,
        idempotency_key="boundary-key",
    )

    with pytest.raises(QuotaExceededError):
        record_usage(
            db=db,
            tenant_id=1,
            usage_type="ai_token",
            quantity=1,
            idempotency_key="over-limit-key",
        )