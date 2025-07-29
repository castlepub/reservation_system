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
    
    # Reservation settings
    MAX_PARTY_SIZE: int = 20
    MIN_RESERVATION_HOURS: int = 0  # Allow same-day bookings
    MAX_RESERVATION_DAYS: int = 90
    
    # Operating hours (will be overridden by database settings)
    OPENING_HOUR: int = 11
    CLOSING_HOUR: int = 23
    
    class Config:
        env_file = ".env"


settings = Settings() 