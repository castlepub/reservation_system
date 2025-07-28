#!/usr/bin/env python3
"""
Simple script to push code to GitHub
"""

import os
import subprocess

def run_command(command):
    """Run a command and return success status"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {command}")
            return True
        else:
            print(f"❌ {command}")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {command} - Error: {e}")
        return False

def main():
    print("🏰 Pushing The Castle Pub Reservation System to GitHub")
    print("=" * 60)
    
    # Check if Git is installed
    if not run_command("git --version"):
        print("❌ Git is not installed. Please install Git first.")
        return
    
    # Create .gitignore if it doesn't exist
    if not os.path.exists('.gitignore'):
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*.so
*.egg
*.egg-info/
dist/
build/
eggs/
parts/
bin/
var/
sdist/
develop-eggs/
.installed.cfg
lib/
lib64/

# Virtual Environment
venv/
env/
ENV/

# Database
*.db
*.sqlite
*.sqlite3

# Environment variables
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Local configuration
local_config.py
"""
        with open('.gitignore', 'w') as f:
            f.write(gitignore_content)
        print("✅ Created .gitignore")
    
    # Initialize Git repository (if not already done)
    if not os.path.exists('.git'):
        run_command("git init")
    
    # Add all files
    run_command("git add .")
    
    # Commit changes
    run_command('git commit -m "Initial commit: The Castle Pub Reservation System"')
    
    # Add remote repository
    run_command("git remote add origin https://github.com/castlepub/reservation_system.git")
    
    # Set main branch
    run_command("git branch -M main")
    
    # Push to GitHub
    if run_command("git push -u origin main"):
        print("\n🎉 Successfully pushed to GitHub!")
        print("📁 View your repository at: https://github.com/castlepub/reservation_system")
        print("\n📋 Next steps:")
        print("1. Visit the repository to verify the code")
        print("2. Set up deployment on Railway")
        print("3. Configure environment variables")
        print("4. Test the deployed system")
    else:
        print("\n❌ Failed to push to GitHub")
        print("Please check your Git configuration and try again")

if __name__ == "__main__":
    main() 