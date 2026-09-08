from dateutil.relativedelta import relativedelta
from datetime import datetime

from sqlalchemy.orm import Session
from app.models.plan import Plan
from app.models.subscription import SubscriptionStatus
from app.models.tenant import Tenant
from sqlalchemy import select
from app.models.subscription import Subscription


"""
Creates and saves a new tenant (customer account) in the database.
The tenant identifies whose resources, subscription, and usage belong to.
Multiple users can belong to a single tenant, and a user can belong to multiple tenants.
"""
def create_tenant(db: Session, name: str) -> Tenant:
    tenant = Tenant(name=name)
    db.add(tenant)
    db.flush() # this is to get the tenant.id before committing, so we can use it for the subscription

    free_plan = db.execute(
        select(Plan).where(Plan.name == "Free")
    ).scalar_one()

    current_period_start = datetime.now()
    current_period_end = current_period_start + relativedelta(months=1)

    # Create a subscription for the new tenant with the free plan
    subscription = Subscription(
        tenant_id=tenant.id,
        plan_id=free_plan.id,
        status=SubscriptionStatus.ACTIVE,
        current_period_start=current_period_start,
        current_period_end=current_period_end,
        paystack_reference=None,
    )
    db.add(subscription)
    db.commit()
    db.refresh(tenant)
    db.refresh(subscription)
    return tenant

# Retrieves a tenant by its ID from the database.
def get_tenant(db: Session, tenant_id: int) -> Tenant | None:
    return db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    ).scalar_one_or_none()

# Retrieve all tenants from the database.
def get_all_tenants(db: Session) -> list[Tenant]:
    return db.execute(select(Tenant)).scalars().all()

# Updates an existing tenant in the database.
def update_tenant(db: Session, tenant_id: int, name: str) -> Tenant | None:
    tenant = get_tenant(db, tenant_id)
    if tenant is None:
        return None
    tenant.name = name
    db.commit()
    db.refresh(tenant)
    return tenant

# Deletes a tenant from the database.
def delete_tenant(db: Session, tenant_id: int) -> bool:
    tenant = get_tenant(db, tenant_id)
    if tenant is None:
        return False
    db.delete(tenant)
    db.commit()
    return True 