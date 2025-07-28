#!/usr/bin/env python3
"""
Simple Railway startup script - minimal version
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main startup function"""
    logger.info("🚀 Starting The Castle Pub Reservation System...")
    
    # Check essential environment variables
    secret_key = os.getenv('SECRET_KEY')
    database_url = os.getenv('DATABASE_URL')
    
    if not secret_key:
        logger.error("❌ SECRET_KEY not set")
        logger.error("Please set SECRET_KEY in Railway environment variables")
        sys.exit(1)
    
    if not database_url:
        logger.error("❌ DATABASE_URL not set")
        logger.error("Please add PostgreSQL service to your Railway project")
        sys.exit(1)
    
    logger.info("✅ Environment variables check passed")
    
    try:
        # Import and start the application
        logger.info("Starting FastAPI application...")
        
        import uvicorn
        port = int(os.getenv('PORT', 8000))
        
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=port,
            workers=1,
            log_level="info",
            access_log=True
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start application: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        sys.exit(1)

if __name__ == "__main__":
    main() 