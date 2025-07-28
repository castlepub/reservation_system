#!/usr/bin/env python3
"""
Check file paths and debug static file serving
"""

import os
import sys

def check_paths():
    print("🔍 Checking file paths...")
    print("=" * 40)
    
    # Current working directory
    cwd = os.getcwd()
    print(f"Current working directory: {cwd}")
    
    # Check if static directory exists
    static_dir = "static"
    static_path = os.path.join(cwd, static_dir)
    print(f"Static directory path: {static_path}")
    print(f"Static directory exists: {os.path.exists(static_path)}")
    
    if os.path.exists(static_path):
        print("Static directory contents:")
        for file in os.listdir(static_path):
            file_path = os.path.join(static_path, file)
            print(f"  - {file} ({os.path.getsize(file_path)} bytes)")
    
    # Check index.html specifically
    index_path = os.path.join(static_path, "index.html")
    print(f"\nIndex.html path: {index_path}")
    print(f"Index.html exists: {os.path.exists(index_path)}")
    
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"Index.html size: {len(content)} characters")
            print(f"Contains 'The Castle Pub': {'The Castle Pub' in content}")
            print(f"Contains 'reservation': {'reservation' in content}")

if __name__ == "__main__":
    check_paths() 