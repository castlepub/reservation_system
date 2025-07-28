#!/usr/bin/env python3
"""
Complete startup script for The Castle Pub Reservation System
"""

import os
import sys
import subprocess
import importlib
import time

def check_package(package_name):
    """Check if a package is installed"""
    try:
        importlib.import_module(package_name)
        return True
    except ImportError:
        return False

def install_package(package_name):
    """Install a package using pip"""
    try:
        print(f"Installing {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name], 
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def install_dependencies():
    """Install required dependencies"""
    print("🔧 Checking and installing dependencies...")
    
    packages = [
        "fastapi",
        "uvicorn[standard]",
        "sqlalchemy",
        "pydantic",
        "email-validator",
        "python-jose[cryptography]",
        "passlib[bcrypt]",
        "python-multipart",
        "jinja2",
        "aiofiles"
    ]
    
    missing_packages = []
    for package in packages:
        base_package = package.split('[')[0]
        if not check_package(base_package):
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Installing {len(missing_packages)} missing packages...")
        for package in missing_packages:
            if install_package(package):
                print(f"✅ {package} installed")
            else:
                print(f"❌ Failed to install {package}")
                return False
    else:
        print("✅ All dependencies are already installed")
    
    return True

def start_server():
    """Start the FastAPI server"""
    print("\n🚀 Starting The Castle Pub Reservation System...")
    print("=" * 50)
    
    # Check if static files exist
    static_dir = "static"
    if not os.path.exists(static_dir):
        print(f"❌ Static directory not found: {static_dir}")
        return False
    
    index_path = os.path.join(static_dir, "index.html")
    if not os.path.exists(index_path):
        print(f"❌ Index.html not found: {index_path}")
        return False
    
    print(f"✅ Static files found: {os.path.abspath(static_dir)}")
    print(f"✅ Index.html found: {len(open(index_path, 'r').read())} characters")
    
    # Import local config
    try:
        import local_config
        print("✅ Local configuration loaded")
    except ImportError as e:
        print(f"❌ Error loading local config: {e}")
        return False
    
    # Import and start the app
    try:
        from app.main import app
        import uvicorn
        
        print("✅ Application imported successfully")
        print("\n🌐 Starting server...")
        print("📱 Server will be available at: http://localhost:8000")
        print("📚 API Documentation: http://localhost:8000/docs")
        print("🔑 Admin login: admin / admin123")
        print("\nPress Ctrl+C to stop the server")
        print("-" * 50)
        
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False

def main():
    print("🏰 The Castle Pub Reservation System")
    print("=" * 50)
    
    # Step 1: Install dependencies
    if not install_dependencies():
        print("\n❌ Failed to install dependencies")
        print("Please try installing them manually:")
        print("pip install fastapi uvicorn sqlalchemy pydantic email-validator")
        return
    
    # Step 2: Start server
    start_server()

if __name__ == "__main__":
    main() 