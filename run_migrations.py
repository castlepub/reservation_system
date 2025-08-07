#!/usr/bin/env python3
"""
Script to run database migrations on Railway
"""

import os
import sys
import subprocess

def run_migrations():
    """Run database migrations"""
    try:
        print("Running database migrations...")
        
        # Run alembic upgrade head
        result = subprocess.run([
            sys.executable, "-m", "alembic", "upgrade", "head"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Migrations completed successfully!")
            print("Output:", result.stdout)
            return True
        else:
            print("❌ Migrations failed!")
            print("Error:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        return False

if __name__ == "__main__":
    success = run_migrations()
    if success:
        print("\n🎉 Database setup completed!")
    else:
        print("\n💥 Database setup failed!")
        sys.exit(1) 