from sqlalchemy.orm import Session

from app.models.tenant import Tenant

"""
Creates and saves a new tenant (customer account) in the database.
The tenant identifies whose resources, subscription, and usage belong to.
Mutiple users can belong to a single tenant, and a user can belong to multiple tenants.
"""
def create_tenant(db: Session, name: str) -> Tenant:
    tenant = Tenant(name=name)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant