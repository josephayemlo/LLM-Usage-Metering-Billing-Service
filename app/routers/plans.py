from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.services.plan_service import get_plan

router = APIRouter(prefix="/plans", tags=["Plans"])

# Endpoint to retrieve an existing plan by its ID from the database.
@router.get("/{plan_id}")
def get_existing_plan(
    plan_id: int,
    db: Session = Depends(get_db),
):
    plan = get_plan(db, plan_id)

    if plan is None:
        raise HTTPException(
            status_code=404,
            detail="Plan not found",
        )

    return plan