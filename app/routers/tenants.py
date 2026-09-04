from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas import TenantCreate, TenantResponse
from app.services.tenant_service import create_tenant


"""
This creates a /tenants/ API endpoint that receives a tenant name, 
saves the tenant to the database, and returns the created tenant.
"""
router = APIRouter(prefix="/tenants", tags=["Tenants"])


@router.post("/", response_model=TenantResponse)
def create_new_tenant(
    tenant: TenantCreate,
    db: Session = Depends(get_db),
):
    return create_tenant(db, tenant.name)