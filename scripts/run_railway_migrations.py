#!/usr/bin/env python3
"""
Script to run Alembic migrations on Railway PostgreSQL database.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extras import RealDictCursor
import subprocess
import json

# Railway PostgreSQL connection details
DB_CONFIG = {
    'host': 'nozomi.proxy.rlwy.net',
    'port': 42902,
    'database': 'railway',
    'user': 'postgres',
    'password': 'JcKlUqURohAAYSSHxfEtkPkfUaurqjSm'
}

def check_current_schema():
    """Check current database schema"""
    print("=== Checking Current Database Schema ===\n")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if reservations table has duration_hours column
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'reservations' 
            AND column_name = 'duration_hours'
        """)
        duration_hours_exists = cursor.fetchone()
        
        # Check if table_layouts table exists
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'table_layouts'
        """)
        table_layouts_exists = cursor.fetchone()
        
        # Check if room_layouts table exists
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'room_layouts'
        """)
        room_layouts_exists = cursor.fetchone()
        
        print("Current Schema Status:")
        print(f"  - duration_hours column in reservations: {'✓' if duration_hours_exists else '❌'}")
        print(f"  - table_layouts table: {'✓' if table_layouts_exists else '❌'}")
        print(f"  - room_layouts table: {'✓' if room_layouts_exists else '❌'}")
        
        cursor.close()
        conn.close()
        
        return {
            'duration_hours_exists': bool(duration_hours_exists),
            'table_layouts_exists': bool(table_layouts_exists),
            'room_layouts_exists': bool(room_layouts_exists)
        }
        
    except Exception as e:
        print(f"❌ Error checking schema: {e}")
        return None

def run_migrations():
    """Run Alembic migrations"""
    print("\n=== Running Alembic Migrations ===\n")
    
    try:
        # Set the database URL environment variable for Alembic
        db_url = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        
        # Run alembic upgrade
        print("Running: alembic upgrade head")
        result = subprocess.run(
            ['alembic', 'upgrade', 'head'],
            env={**os.environ, 'DATABASE_URL': db_url},
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        if result.returncode == 0:
            print("✓ Migrations completed successfully!")
            print("Output:")
            print(result.stdout)
        else:
            print("❌ Migration failed!")
            print("Error:")
            print(result.stderr)
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Railway Database Migration Script")
    print("=" * 50)
    
    # Check current schema
    schema_status = check_current_schema()
    if schema_status is None:
        print("❌ Failed to check schema. Exiting.")
        return
    
    # Check if migrations are needed
    needs_migration = not all([
        schema_status['duration_hours_exists'],
        schema_status['table_layouts_exists'],
        schema_status['room_layouts_exists']
    ])
    
    if not needs_migration:
        print("\n✅ Database schema is up to date!")
        return
    
    print(f"\n⚠️  Database needs migration. Running migrations...")
    
    # Run migrations
    success = run_migrations()
    
    if success:
        print("\n=== Final Schema Check ===")
        final_status = check_current_schema()
        
        if final_status and all([
            final_status['duration_hours_exists'],
            final_status['table_layouts_exists'],
            final_status['room_layouts_exists']
        ]):
            print("\n🎉 All migrations completed successfully!")
        else:
            print("\n⚠️  Some migrations may have failed. Please check manually.")
    else:
        print("\n❌ Migration failed. Please check the errors above.")

if __name__ == "__main__":
    main() 