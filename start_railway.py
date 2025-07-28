#!/usr/bin/env python3
"""
Railway startup script for The Castle Pub Reservation System
"""

import os
import sys
import time
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if required environment variables are set"""
    required_vars = ['SECRET_KEY']
    missing_vars = []
    
    # Check for database connection
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        # Check for individual PostgreSQL variables
        pg_host = os.getenv('PGHOST')
        pg_user = os.getenv('PGUSER')
        pg_password = os.getenv('PGPASSWORD')
        pg_database = os.getenv('PGDATABASE')
        
        if not all([pg_host, pg_user, pg_password, pg_database]):
            missing_vars.append('DATABASE_URL or PostgreSQL variables')
        else:
            logger.info("✓ PostgreSQL environment variables found")
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        logger.error("Please set SECRET_KEY in your Railway dashboard")
        logger.error("Make sure PostgreSQL service is added to your project")
        return False
    
    logger.info("✓ Environment variables check passed")
    return True

def initialize_database():
    """Initialize database tables"""
    try:
        from app.core.database import engine, Base
        from sqlalchemy import text
        
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        
        logger.info("Testing database connection...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info(f"Database test result: {result.fetchone()}")
        
        logger.info("✓ Database initialization successful")
        return True
        
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Full error details: {e}")
        return False

def main():
    """Main startup function"""
    logger.info("🚀 Starting The Castle Pub Reservation System...")
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Initialize database
    if not initialize_database():
        logger.error("Failed to initialize database. Exiting...")
        sys.exit(1)
    
    logger.info("✓ All startup checks passed")
    logger.info("Starting FastAPI application...")
    
    # Start the FastAPI application
    import uvicorn
    port = int(os.getenv('PORT', 8000))
    
    logger.info(f"Starting uvicorn on port {port}")
    logger.info("Application should be available at /health endpoint")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        workers=1,
        log_level="info"
    )

if __name__ == "__main__":
    main() 