#!/usr/bin/env python3
"""
Setup script to initialize Git repository and push to GitHub
"""

import os
import subprocess
import sys

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - Success")
            return True
        else:
            print(f"❌ {description} - Failed")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - Error: {e}")
        return False

def create_gitignore():
    """Create .gitignore file"""
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

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

# Temporary files
*.tmp
*.temp

# Local configuration
local_config.py
"""
    
    with open('.gitignore', 'w') as f:
        f.write(gitignore_content)
    print("✅ Created .gitignore file")

def create_readme():
    """Create or update README.md"""
    readme_content = """# 🏰 The Castle Pub Reservation System

A modern, full-featured restaurant reservation system built with FastAPI and PostgreSQL, designed to replace Teburio for The Castle Pub.

## 🌟 Features

- **Beautiful Web Interface**: Modern, responsive design with castle theme
- **Admin Dashboard**: Complete management interface for staff
- **Public API**: Integration ready for chatbot and website
- **Smart Table Assignment**: Automatic table combination logic
- **Email Confirmations**: SendGrid integration for booking confirmations
- **Daily Reports**: PDF generation for daily reservation slips
- **JWT Authentication**: Secure admin access
- **Real-time Availability**: Live availability checking

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/castlepub/reservation_system.git
   cd reservation_system
   ```

2. **Install dependencies**
   ```bash
   python start_system.py
   ```

3. **Access the application**
   - **Main Website**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs
   - **Admin Login**: admin / admin123

## 📁 Project Structure

```
reservation_system/
├── app/                    # Main application code
│   ├── api/               # API endpoints
│   ├── core/              # Configuration and database
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Pydantic schemas
│   └── services/          # Business logic
├── static/                # Web interface files
│   ├── index.html         # Main page
│   ├── styles.css         # Styling
│   └── script.js          # Frontend logic
├── scripts/               # Utility scripts
├── alembic/               # Database migrations
└── requirements.txt       # Python dependencies
```

## 🔧 Configuration

Copy `.env.example` to `.env` and configure:

```env
DATABASE_URL=postgresql://user:password@localhost/castle_reservations
SECRET_KEY=your-secret-key
SENDGRID_API_KEY=your-sendgrid-key
FRONTEND_URL=https://reservations.thecastle.de
```

## 📚 API Documentation

- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **API Guide**: See `API_DOCUMENTATION.md`

## 🎨 Web Interface

The system includes a beautiful, responsive web interface:

- **Modern Design**: Purple gradient theme with castle aesthetics
- **Mobile Responsive**: Works perfectly on all devices
- **Real-time Updates**: Live availability checking
- **Admin Dashboard**: Tabbed interface for management

## 🔐 Security

- JWT-based authentication
- Password hashing with bcrypt
- CORS middleware
- Rate limiting on public endpoints
- Secure token-based reservation management

## 🚀 Deployment

### Railway (Recommended)
1. Connect your GitHub repository to Railway
2. Set environment variables
3. Deploy automatically

### Manual Deployment
1. Install dependencies: `pip install -r requirements.txt`
2. Set up PostgreSQL database
3. Configure environment variables
4. Run migrations: `alembic upgrade head`
5. Start server: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is proprietary software for The Castle Pub.

## 🆘 Support

For support, contact the development team or create an issue in this repository.

---

**Built with ❤️ for The Castle Pub**
"""
    
    with open('README.md', 'w') as f:
        f.write(readme_content)
    print("✅ Created README.md file")

def setup_git_repository():
    """Set up Git repository and push to GitHub"""
    print("🚀 Setting up Git repository...")
    
    # Create .gitignore and README
    create_gitignore()
    create_readme()
    
    # Initialize Git repository
    if not run_command("git init", "Initializing Git repository"):
        return False
    
    # Add all files
    if not run_command("git add .", "Adding files to Git"):
        return False
    
    # Create initial commit
    if not run_command('git commit -m "Initial commit: The Castle Pub Reservation System"', "Creating initial commit"):
        return False
    
    # Add remote repository
    if not run_command("git remote add origin https://github.com/castlepub/reservation_system.git", "Adding remote repository"):
        return False
    
    # Push to main branch
    if not run_command("git branch -M main", "Setting main branch"):
        return False
    
    if not run_command("git push -u origin main", "Pushing to GitHub"):
        return False
    
    print("\n🎉 Repository setup complete!")
    print("📁 View your repository at: https://github.com/castlepub/reservation_system")
    return True

def main():
    print("🏰 The Castle Pub Reservation System - Repository Setup")
    print("=" * 60)
    
    # Check if Git is installed
    if not run_command("git --version", "Checking Git installation"):
        print("❌ Git is not installed. Please install Git first.")
        return
    
    # Setup repository
    if setup_git_repository():
        print("\n✅ Successfully pushed to GitHub!")
        print("\n📋 Next steps:")
        print("1. Visit: https://github.com/castlepub/reservation_system")
        print("2. Set up deployment (Railway recommended)")
        print("3. Configure environment variables")
        print("4. Test the system")
    else:
        print("\n❌ Failed to set up repository")
        print("Please check your Git configuration and try again")

if __name__ == "__main__":
    main() 