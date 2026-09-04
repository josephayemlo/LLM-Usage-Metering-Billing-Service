from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.plan import Plan

# Retrieves a plan by its ID from the database.
def get_plan(db: Session, plan_id: int) -> Plan | None:
    return db.execute(
        select(Plan).where(Plan.id == plan_id)
    ).scalar_one_or_none()