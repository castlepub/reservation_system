import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Get DATABASE_URL from environment or config
database_url = os.getenv("DATABASE_URL", settings.DATABASE_URL)

# Create database engine
if database_url.startswith("sqlite"):
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
else:
    engine = create_engine(database_url)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 