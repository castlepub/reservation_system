#!/usr/bin/env python3
"""
Ultra-simple Railway startup script
"""
import os
import sys
import uvicorn
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    print("🚀 Starting ultra-simple Railway deployment...")
    
    # Set default environment variables
    os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
    os.environ.setdefault("SECRET_KEY", "default-secret-key")
    os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    
    print("✅ Environment variables set")
    
    try:
        # Import the simple app
        from app.main_simple import app
        print("✅ Simple app imported successfully")
        
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