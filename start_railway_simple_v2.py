#!/usr/bin/env python3
"""
Simple Railway startup script - Version 2
"""
import os
import sys
import uvicorn
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    print("🚀 Starting Railway deployment...")
    
    # Set default environment variables if not present
    if not os.getenv("DATABASE_URL"):
        print("⚠️ DATABASE_URL not set, using default")
        os.environ["DATABASE_URL"] = "sqlite:///./test.db"
    
    if not os.getenv("SECRET_KEY"):
        print("⚠️ SECRET_KEY not set, using default")
        os.environ["SECRET_KEY"] = "default-secret-key-for-development"
    
    if not os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"):
        print("⚠️ ACCESS_TOKEN_EXPIRE_MINUTES not set, using default")
        os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
    
    print("✅ Environment variables configured")
    
    try:
        # Import and start the app
        from app.main import app
        print("✅ App imported successfully")
        
        # Get port from Railway
        port = int(os.getenv("PORT", 8000))
        host = "0.0.0.0"
        
        print(f"🌐 Starting server on {host}:{port}")
        
        # Start the server
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info"
        )
        
    except Exception as e:
        print(f"❌ Failed to start app: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 