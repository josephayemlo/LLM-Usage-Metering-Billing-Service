from fastapi import FastAPI, Depends
from app.database import engine
from app.dependencies import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.routers.tenants import router as tenant_router
from app.routers.plans import router as plan_router
from app.routers.subscriptions import router as subscription_router
from app.routers.usage import router as usage_router

app = FastAPI()
app.include_router(tenant_router)
app.include_router(plan_router)
app.include_router(subscription_router)
app.include_router(usage_router)


# Root endpoint — confirms that the API is running
@app.get("/")
def root():
    return {"message": "Usage Metering and Billing API"}


# Health-check endpoint — used to confirm that the API is responding
@app.get("/health")
def health():
    return {"status": "healthy"}


# Database test endpoint — attempts to establish a connection to PostgreSQL
@app.get("/db-test")
def db_test(db: Session = Depends(get_db)):
    return {"database": "connected"}