#!/usr/bin/env python3
"""
Restart the server with debugging
"""

import os
import sys
import subprocess
import time

def restart_server():
    print("🔄 Restarting The Castle Pub Reservation System...")
    print("=" * 50)
    
    # Check paths first
    print("📁 Checking file paths:")
    cwd = os.getcwd()
    static_path = os.path.join(cwd, "static")
    index_path = os.path.join(static_path, "index.html")
    
    print(f"  Working directory: {cwd}")
    print(f"  Static directory: {static_path}")
    print(f"  Static exists: {os.path.exists(static_path)}")
    print(f"  Index.html exists: {os.path.exists(index_path)}")
    
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"  Index.html size: {len(content)} characters")
    
    print("\n🚀 Starting server...")
    print("Press Ctrl+C to stop")
    print("-" * 50)
    
    # Start the server
    try:
        subprocess.run([
            sys.executable, "-c", 
            "import local_config; import uvicorn; from app.main import app; uvicorn.run(app, host='0.0.0.0', port=8000, log_level='info')"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")

if __name__ == "__main__":
    restart_server() 