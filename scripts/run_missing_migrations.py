#!/usr/bin/env python3
"""
Script to ensure all database migrations are applied, especially for table_layouts
"""
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alembic.config import Config
from alembic import command
from app.core.database import engine
from sqlalchemy import text

def check_table_exists(table_name):
    """Check if a table exists in the database"""
    try:
        with engine.connect() as conn:
            # For PostgreSQL
            result = conn.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table_name}'
                );
            """))
            return result.scalar()
    except Exception:
        try:
            # For SQLite
            with engine.connect() as conn:
                result = conn.execute(text(f"""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='{table_name}';
                """))
                return result.fetchone() is not None
        except Exception as e:
            print(f"Error checking table existence: {e}")
            return False

def check_column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    try:
        with engine.connect() as conn:
            # For PostgreSQL
            result = conn.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = '{table_name}' 
                    AND column_name = '{column_name}'
                );
            """))
            return result.scalar()
    except Exception:
        try:
            # For SQLite
            with engine.connect() as conn:
                result = conn.execute(text(f"PRAGMA table_info({table_name})"))
                columns = [row[1] for row in result.fetchall()]
                return column_name in columns
        except Exception as e:
            print(f"Error checking column existence: {e}")
            return False

def main():
    print("🔍 Checking database schema...")
    
    # Check critical tables
    tables_to_check = ['tables', 'table_layouts', 'reservations', 'reservations_tables']
    for table in tables_to_check:
        exists = check_table_exists(table)
        print(f"Table '{table}': {'✓ EXISTS' if exists else '✗ MISSING'}")
    
    # Check specific column that's causing issues
    if check_table_exists('table_layouts'):
        custom_capacity_exists = check_column_exists('table_layouts', 'custom_capacity')
        print(f"Column 'table_layouts.custom_capacity': {'✓ EXISTS' if custom_capacity_exists else '✗ MISSING'}")
    
    print("\n🚀 Running Alembic migrations...")
    
    try:
        # Configure Alembic
        alembic_cfg = Config("alembic.ini")
        
        # Run upgrade to head
        command.upgrade(alembic_cfg, "head")
        print("✅ All migrations applied successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return 1
    
    print("\n🔍 Re-checking schema after migrations...")
    
    # Re-check the problematic column
    if check_table_exists('table_layouts'):
        custom_capacity_exists = check_column_exists('table_layouts', 'custom_capacity')
        print(f"Column 'table_layouts.custom_capacity': {'✓ EXISTS' if custom_capacity_exists else '✗ STILL MISSING'}")
        
        if not custom_capacity_exists:
            print("\n⚠️  WARNING: custom_capacity column still missing after migration!")
            print("This might require manual database intervention.")
    
    return 0

if __name__ == "__main__":
    exit(main())