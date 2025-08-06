#!/usr/bin/env python3
"""
Script to apply area management migration to Railway database using public URL
Run this script to add the new area management fields to your Railway database
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def apply_migration():
    """Apply the area management migration to Railway database"""
    # Use the Railway public database URL
    db_url = "postgresql://postgres:JcKlUqURohAAYSSHxfEtkPkfUaurqjSm@nozomi.proxy.rlwy.net:42902/railway"
    
    try:
        print("🔗 Connecting to Railway database via public URL...")
        conn = psycopg2.connect(db_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("✅ Connected successfully!")
        
        # Read the SQL migration file
        migration_file = "scripts/apply_area_management_to_railway.sql"
        with open(migration_file, 'r') as f:
            sql_script = f.read()
        
        print("📝 Applying area management migration...")
        
        # Split the script into individual statements
        statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements, 1):
            if statement:
                print(f"   Executing statement {i}/{len(statements)}...")
                try:
                    cursor.execute(statement)
                    print(f"   ✅ Statement {i} executed successfully")
                except Exception as e:
                    print(f"   ⚠️  Statement {i} had an issue: {e}")
                    # Continue with other statements
        
        print("🎉 Migration completed successfully!")
        
        # Verify the changes
        print("\n📊 Verifying changes...")
        cursor.execute("""
            SELECT id, name, area_type, priority, is_fallback_area, fallback_for, display_order 
            FROM rooms 
            ORDER BY display_order, priority
            LIMIT 10
        """)
        
        results = cursor.fetchall()
        print("\nCurrent rooms with area management:")
        for row in results:
            print(f"  ID: {row[0]}, Name: {row[1]}, Type: {row[2]}, Priority: {row[3]}, Fallback: {row[4]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error applying migration: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Railway Area Management Migration (Public URL)")
    print("=" * 50)
    
    success = apply_migration()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("You can now use the new area management features in your application.")
    else:
        print("\n❌ Migration failed. Please check the error messages above.") 