#!/usr/bin/env python3
"""
Test script to run The Castle Pub Reservation System locally
"""

import sys
import os

# Import local configuration
import local_config

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("🏰 The Castle Pub Reservation System")
    print("=" * 40)
    
    try:
        # Import and run the application
        from app.main import app
        import uvicorn
        
        print("✓ Application loaded successfully")
        print("✓ Database configured for SQLite")
        print("✓ Starting server...")
        print("\n🌐 Server will be available at: http://localhost:8000")
        print("📚 API Documentation: http://localhost:8000/docs")
        print("📖 ReDoc Documentation: http://localhost:8000/redoc")
        print("🔑 Admin login: admin / admin123")
        print("\nPress Ctrl+C to stop the server")
        print("-" * 50)
        
        # Start the server
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("Please make sure all dependencies are installed:")
        print("pip install fastapi uvicorn sqlalchemy pydantic")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 