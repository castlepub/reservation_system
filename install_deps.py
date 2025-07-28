#!/usr/bin/env python3
"""
Install required dependencies for The Castle Pub Reservation System
"""

import subprocess
import sys
import importlib

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
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    print("🔧 Installing Dependencies for The Castle Pub Reservation System")
    print("=" * 60)
    
    # Required packages
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
    
    print("Checking current installations...")
    missing_packages = []
    
    for package in packages:
        # Extract base package name (remove [extras])
        base_package = package.split('[')[0]
        if check_package(base_package):
            print(f"✅ {package} - Already installed")
        else:
            print(f"❌ {package} - Missing")
            missing_packages.append(package)
    
    if not missing_packages:
        print("\n🎉 All dependencies are already installed!")
        return
    
    print(f"\n📦 Installing {len(missing_packages)} missing packages...")
    
    for package in missing_packages:
        print(f"Installing {package}...")
        if install_package(package):
            print(f"✅ {package} - Installed successfully")
        else:
            print(f"❌ {package} - Failed to install")
    
    print("\n🔍 Final check...")
    all_installed = True
    for package in packages:
        base_package = package.split('[')[0]
        if check_package(base_package):
            print(f"✅ {package} - Ready")
        else:
            print(f"❌ {package} - Still missing")
            all_installed = False
    
    if all_installed:
        print("\n🎉 All dependencies installed successfully!")
        print("You can now run: python restart_server.py")
    else:
        print("\n⚠️ Some dependencies failed to install.")
        print("Please try installing them manually:")
        for package in packages:
            base_package = package.split('[')[0]
            if not check_package(base_package):
                print(f"pip install {package}")

if __name__ == "__main__":
    main() 