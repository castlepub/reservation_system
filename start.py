#!/usr/bin/env python3
"""
Startup script for The Castle Pub Reservation System
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import psycopg2
        print("✓ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_env_file():
    """Check if .env file exists"""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  .env file not found")
        print("Please copy env.example to .env and configure your settings")
        return False
    print("✓ .env file found")
    return True

def init_database():
    """Initialize the database with sample data"""
    try:
        print("Initializing database...")
        result = subprocess.run([sys.executable, "scripts/init_db.py"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Database initialized successfully")
            return True
        else:
            print(f"✗ Database initialization failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        return False

def start_server():
    """Start the FastAPI server"""
    print("Starting The Castle Pub Reservation System...")
    print("Server will be available at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\nServer stopped")

def main():
    """Main startup function"""
    print("The Castle Pub Reservation System")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check environment file
    if not check_env_file():
        print("Continuing without .env file (using defaults)")
    
    # Initialize database
    if not init_database():
        print("Continuing without database initialization")
    
    # Start server
    start_server()

if __name__ == "__main__":
    main() 