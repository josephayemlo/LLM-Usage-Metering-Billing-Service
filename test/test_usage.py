from fastapi.testclient import TestClient

from app.main import app
from app.dependencies import get_db
from datetime import datetime, timedelta
from sqlalchemy.pool import StaticPool
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.tenant import Tenant
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.models.usage_event import UsageEvent
from app.services.usage_service import record_usage
from app.services.quota_service import QuotaExceededError


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

    tenant = Tenant(name="Test Tenant")

    free_plan = Plan(
        name="Free",
        api_call_limit=1000,
        ai_token_limit=100,
        price_kobo=0,
        billing_interval="monthly",
    )

    pro_plan = Plan(
        name="Pro",
        api_call_limit=10000,
        ai_token_limit=1000,
        price_kobo=500000,
        billing_interval="monthly",
    )

    session.add_all([tenant, free_plan, pro_plan])
    session.commit()

    subscription = Subscription(
        tenant_id=tenant.id,
        plan_id=free_plan.id,
        status="active",
        current_period_start=datetime.now() - timedelta(days=1),
        current_period_end=datetime.now() + timedelta(days=29),
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

    events = db.query(UsageEvent).all()

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

def test_usage_outside_billing_period_is_not_counted(db):
    from datetime import datetime, timedelta

    from app.models.usage_event import UsageEvent
    from app.services.usage_query_service import get_usage_total

    old_event = UsageEvent(
        tenant_id=1,
        usage_type="ai_token",
        quantity=100,
        idempotency_key="old-event",
        created_at=datetime.now() - timedelta(days=10),
    )

    db.add(old_event)
    db.commit()

    subscription = db.query(Subscription).first()

    total = get_usage_total(
        db=db,
        tenant_id=1,
        usage_type="ai_token",
        period_start=subscription.current_period_start,
        period_end=subscription.current_period_end,
    )

    assert total == 0


def test_ai_usage_cost_is_persisted(db):
    from app.models.usage_event import UsageEvent

    usage_event = UsageEvent(
        tenant_id=1,
        usage_type="ai_token",
        quantity=22,
        idempotency_key="cost-test",
        cost_micro_units=42,
    )

    db.add(usage_event)
    db.commit()
    db.refresh(usage_event)

    saved_event = db.query(UsageEvent).filter(
        UsageEvent.id == usage_event.id
    ).first()

    assert saved_event.cost_micro_units == 42

def test_generate_persists_ai_cost(client, db):
    response = client.post(
        "/generate/",
        json={
            "tenant_id": 1,
            "prompt": "hello world",
        },
        headers={
            "idempotency-key": "generate-cost-test",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["cost_micro_units"] == 42

    from app.models.usage_event import UsageEvent

    usage_event = db.query(UsageEvent).filter(
        UsageEvent.idempotency_key == "generate-cost-test"
    ).first()

    assert usage_event is not None
    assert usage_event.cost_micro_units == 42