#!/usr/bin/env python3
"""
Script to set up the database schema on Railway
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_database():
    """Set up the database schema"""
    try:
        print("Setting up database schema...")
        
        # Change to the project directory
        project_dir = Path(__file__).parent
        os.chdir(project_dir)
        
        # Run alembic upgrade head
        print("Running database migrations...")
        result = subprocess.run([
            sys.executable, "-m", "alembic", "upgrade", "head"
        ], capture_output=True, text=True, cwd=project_dir)
        
        if result.returncode == 0:
            print("✅ Database migrations completed successfully!")
            print("Output:", result.stdout)
            
            # Test the connection
            print("\nTesting database connection...")
            test_result = subprocess.run([
                sys.executable, "test_db_connection.py"
            ], capture_output=True, text=True, cwd=project_dir)
            
            if test_result.returncode == 0:
                print("✅ Database connection test passed!")
                print("Output:", test_result.stdout)
                return True
            else:
                print("❌ Database connection test failed!")
                print("Error:", test_result.stderr)
                return False
        else:
            print("❌ Database migrations failed!")
            print("Error:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        return False

if __name__ == "__main__":
    success = setup_database()
    if success:
        print("\n🎉 Database setup completed successfully!")
    else:
        print("\n💥 Database setup failed!")
        sys.exit(1) 