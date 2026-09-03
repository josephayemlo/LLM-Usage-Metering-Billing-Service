from fastapi import FastAPI
from app.database import engine

# Create the FastAPI application instance
app = FastAPI()


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
def db_test():
    with engine.connect() as connection:
        return {"database": "connected"}