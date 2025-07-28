from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost/castle_reservations"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Email (SendGrid)
    SENDGRID_API_KEY: Optional[str] = None
    SENDGRID_FROM_EMAIL: str = "noreply@thecastle.de"
    
    # Frontend
    FRONTEND_URL: str = "https://reservations.thecastle.de"
    
    # Redis (for background tasks)
    REDIS_URL: str = "redis://localhost:6379"
    
    # Business Logic
    RESERVATION_TOKEN_EXPIRE_DAYS: int = 30
    MAX_PARTY_SIZE: int = 20
    MIN_RESERVATION_HOURS: int = 2  # Minimum hours in advance
    MAX_RESERVATION_DAYS: int = 90  # Maximum days in advance
    
    # Operating Hours (24-hour format)
    OPENING_HOUR: int = 11  # 11:00 AM
    CLOSING_HOUR: int = 23  # 11:00 PM
    
    class Config:
        env_file = ".env"


settings = Settings() 