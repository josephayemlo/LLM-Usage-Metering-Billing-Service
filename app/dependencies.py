from collections.abc import Generator

from app.database import SessionLocal

# Dependency function to provide a database session for FastAPI endpoints.
"""
It opens a SQLAlchemy session so the endpoint can communicate with the database, 
then automatically closes that session when the request is finished.
"""
def get_db() -> Generator:
    db = SessionLocal()
    # print("DB session opened")
    try:
        yield db
    finally:
        db.close()
        # print("DB session closed")