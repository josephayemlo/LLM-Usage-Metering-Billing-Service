from sqlalchemy.orm import Session
from app.models.tenant import Tenant
from sqlalchemy import select
"""
Creates and saves a new tenant (customer account) in the database.
The tenant identifies whose resources, subscription, and usage belong to.
Multiple users can belong to a single tenant, and a user can belong to multiple tenants.
"""
def create_tenant(db: Session, name: str) -> Tenant:
    tenant = Tenant(name=name)
    db.add(tenant)
    db.commit()
    # print(f"Tenant created: {tenant.name} (ID: {tenant.id})")
    db.refresh(tenant)
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