from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas import TenantCreate, TenantResponse
from app.services.tenant_service import (
    create_tenant,
    get_tenant,
    get_all_tenants,
    update_tenant,
    delete_tenant
)

"""
This creates a /tenants/ API endpoint that receives a tenant name, 
saves the tenant to the database, and returns the created tenant.
"""
router = APIRouter(prefix="/tenants", tags=["Tenants"])

# Endpoint to create a new tenant (customer account) in the database.
@router.post("/", response_model=TenantResponse)
def create_new_tenant(
    tenant: TenantCreate,
    db: Session = Depends(get_db),
):
    return create_tenant(db, tenant.name)

# Endpoint to retrieve an existing tenant by its ID from the database.
@router.get("/{tenant_id}", response_model=TenantResponse)
def get_existing_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
):
    tenant = get_tenant(db, tenant_id)

    if tenant is None:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found",
        )

    return tenant
# Endpoint to retrieve all tenants from the database.
@router.get("/", response_model=list[TenantResponse])
def get_all_existing_tenants(
    db: Session = Depends(get_db),
):
    return get_all_tenants(db)

# Endpoint to update an existing tenant in the database.
@router.put("/{tenant_id}", response_model=TenantResponse)
def update_existing_tenant(
    tenant_id: int,
    tenant: TenantCreate,
    db: Session = Depends(get_db),
):
    updated_tenant = update_tenant(db, tenant_id, tenant.name)

    if updated_tenant is None:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found",
        )

    return updated_tenant   
# Endpoint to delete an existing tenant from the database.
@router.delete("/{tenant_id}")
def delete_existing_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
):
    success = delete_tenant(db, tenant_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found",
        )

    return {"message": "Tenant deleted successfully"}   