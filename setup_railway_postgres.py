#!/usr/bin/env python3
"""
Railway PostgreSQL Setup Helper
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_railway_postgres():
    """Check if PostgreSQL is properly configured on Railway"""
    
    print("🔍 Checking Railway PostgreSQL Configuration...")
    print("=" * 50)
    
    # Check for DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        print(f"✅ DATABASE_URL found: {database_url[:50]}...")
    else:
        print("❌ DATABASE_URL not found")
    
    # Check for individual PostgreSQL variables
    pg_vars = {
        'PGHOST': os.getenv('PGHOST'),
        'PGPORT': os.getenv('PGPORT'),
        'PGUSER': os.getenv('PGUSER'),
        'PGPASSWORD': os.getenv('PGPASSWORD'),
        'PGDATABASE': os.getenv('PGDATABASE')
    }
    
    print("\n📊 PostgreSQL Environment Variables:")
    for var, value in pg_vars.items():
        if value:
            if 'PASSWORD' in var:
                print(f"  ✅ {var}: {'*' * len(value)}")
            else:
                print(f"  ✅ {var}: {value}")
        else:
            print(f"  ❌ {var}: Not set")
    
    # Check if we have enough info to connect
    if database_url or all(pg_vars.values()):
        print("\n✅ PostgreSQL configuration looks good!")
        return True
    else:
        print("\n❌ PostgreSQL not properly configured")
        return False

def print_setup_instructions():
    """Print setup instructions for Railway PostgreSQL"""
    
    print("\n" + "=" * 50)
    print("🚀 RAILWAY POSTGRESQL SETUP INSTRUCTIONS")
    print("=" * 50)
    
    print("""
1. Go to your Railway project dashboard
2. Click "New Service"
3. Select "Database" → "PostgreSQL"
4. Wait for Railway to provision the database
5. Railway will automatically connect your app to the database
6. The DATABASE_URL will be automatically set

After adding PostgreSQL:
- Your app will automatically get the DATABASE_URL
- Tables will be created on first startup
- Health check will test the database connection

Required Environment Variables to set manually:
- SECRET_KEY (required for JWT tokens)

Optional Environment Variables:
- ALGORITHM=HS256
- ACCESS_TOKEN_EXPIRE_MINUTES=30
- SENDGRID_API_KEY (for email confirmations)
- SENDGRID_FROM_EMAIL=noreply@thecastle.de
""")

def test_database_connection():
    """Test the database connection"""
    try:
        from app.core.database import engine
        from sqlalchemy import text
        
        print("\n🔗 Testing database connection...")
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Database connected successfully!")
            print(f"   PostgreSQL version: {version}")
            return True
            
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False

def main():
    """Main function"""
    
    print("🏰 The Castle Pub - Railway PostgreSQL Setup")
    print("=" * 50)
    
    # Check current configuration
    if not check_railway_postgres():
        print_setup_instructions()
        sys.exit(1)
    
    # Test connection if possible
    if os.getenv('DATABASE_URL') or all([os.getenv('PGHOST'), os.getenv('PGUSER'), os.getenv('PGPASSWORD'), os.getenv('PGDATABASE')]):
        print("\n🧪 Testing database connection...")
        if test_database_connection():
            print("\n🎉 Everything is set up correctly!")
            print("Your Railway deployment should work now!")
        else:
            print("\n⚠️  Database connection failed. Check Railway logs.")
    else:
        print_setup_instructions()

if __name__ == "__main__":
    main() 