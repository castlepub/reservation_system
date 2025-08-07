import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Import routers - testing one by one
try:
    from app.api.auth import router as auth_router
    print("✅ Auth router imported successfully")
except Exception as e:
    print(f"❌ Auth router failed: {e}")
    auth_router = None

try:
    from app.api.admin import router as admin_router
    print("✅ Admin router imported successfully")
except Exception as e:
    print(f"❌ Admin router failed: {e}")
    admin_router = None

try:
    from app.api.settings import router as settings_router
    print("✅ Settings router imported successfully")
except Exception as e:
    print(f"❌ Settings router failed: {e}")
    settings_router = None

try:
    from app.api.public import router as public_router
    print("✅ Public router imported successfully")
except Exception as e:
    print(f"❌ Public router failed: {e}")
    public_router = None

try:
    from app.api.dashboard import router as dashboard_router
    print("✅ Dashboard router imported successfully")
except Exception as e:
    print(f"❌ Dashboard router failed: {e}")
    dashboard_router = None

try:
    from app.api.layout import router as layout_router
    print("✅ Layout router imported successfully")
except Exception as e:
    print(f"❌ Layout router failed: {e}")
    layout_router = None

# Create FastAPI app
app = FastAPI(title="The Castle Pub Reservation System")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers - only if they imported successfully
if auth_router:
    app.include_router(auth_router, prefix="/api")
    print("✅ Auth router included")

if admin_router:
    app.include_router(admin_router, prefix="/admin")
    print("✅ Admin router included")

if settings_router:
    app.include_router(settings_router, prefix="/api")
    print("✅ Settings router included")

if public_router:
    app.include_router(public_router, prefix="/api")
    print("✅ Public router included")

if dashboard_router:
    app.include_router(dashboard_router, prefix="/api")
    print("✅ Dashboard router included")

if layout_router:
    app.include_router(layout_router, prefix="/api/layout")
    print("✅ Layout router included")

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
try:
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
except Exception:
    pass  # Ignore static file mounting errors

@app.get("/")
async def root():
    """Serve the main HTML file"""
    try:
        html_file = os.path.join(static_dir, "index.html")
        if os.path.exists(html_file):
            return FileResponse(html_file)
    except Exception:
        pass
    return {"message": "The Castle Pub Reservation System", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint for Railway"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"message": "pong", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api")
async def api_root():
    """API root endpoint"""
    return {"message": "The Castle Pub Reservation System API", "status": "running"}

@app.get("/api/debug/db-test")
async def test_database_connection():
    """Test database connection without dependencies"""
    try:
        from app.core.database import get_db
        from sqlalchemy.orm import Session
        
        # Try to get a database session
        db_gen = get_db()
        db = next(db_gen)
        
        # Try a simple query
        from sqlalchemy import text
        result = db.execute(text("SELECT 1 as test"))
        test_result = result.fetchone()
        
        return {
            "status": "success",
            "message": "Database connection working",
            "test_query_result": test_result.test if test_result else None
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Database connection failed: {str(e)}",
            "error_type": type(e).__name__
        }

@app.get("/api/setup-database")
async def setup_database():
    """Set up database tables if they don't exist"""
    try:
        from app.core.database import engine
        from app.models import user, room, table, reservation, settings
        from sqlalchemy import text
        
        # Test connection first
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ Database connection working!")
            
            # Create all tables
            from app.core.database import Base
            Base.metadata.create_all(bind=engine)
            print("✅ Database tables created!")
            
            # Test if we can query tables
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            print(f"✅ Found {len(tables)} tables: {tables}")
            
            return {
                "status": "success",
                "message": "Database setup completed",
                "tables": tables
            }
            
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Database setup failed: {str(e)}",
            "error_type": type(e).__name__
        }