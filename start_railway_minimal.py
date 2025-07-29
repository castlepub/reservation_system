#!/usr/bin/env python3
"""
Minimal Railway startup script - get the app running first, handle DB later
"""

import os
import sys
from datetime import datetime

def log(message):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)

def main():
    """Start the application with minimal checks"""
    log("🚀 Starting Castle Pub Reservation System (Minimal Mode)...")
    
    # Set default environment variables if missing
    if not os.getenv("PORT"):
        os.environ["PORT"] = "8000"
        log("⚠️ PORT not set, using default 8000")
    
    if not os.getenv("SECRET_KEY"):
        os.environ["SECRET_KEY"] = "temporary-secret-key-for-startup"
        log("⚠️ SECRET_KEY not set, using temporary key")
    
    # Try to start the app immediately
    try:
        log("📦 Importing FastAPI app...")
        import uvicorn
        from app.main import app
        
        log("✅ FastAPI app imported successfully")
        
        port = int(os.getenv("PORT", 8000))
        log(f"🌐 Starting server on port {port}...")
        
        # Start the server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info",
            access_log=True
        )
        
    except ImportError as e:
        log(f"❌ Import error: {e}")
        log("💡 This might be a dependency issue")
        sys.exit(1)
    except Exception as e:
        log(f"❌ Startup error: {e}")
        log("💡 Check the logs above for more details")
        sys.exit(1)

if __name__ == "__main__":
    main() 