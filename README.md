# The Castle Pub Reservation System

A comprehensive restaurant reservation system built with FastAPI and PostgreSQL, designed to replace Teburio for The Castle Pub.

## Features

- **Admin Dashboard**: Secure JWT-based authentication with role management
- **Reservation Management**: Create, edit, cancel, and search reservations
- **Table Management**: Multi-room table system with automatic table combination
- **Public API**: Integration endpoints for chatbot and website
- **Email Confirmations**: Automated emails with cancel/reschedule links
- **Daily PDF Reports**: Printable reservation slips for staff
- **Real-time Availability**: Check available time slots and table combinations

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Authentication**: JWT with PyJWT
- **Email**: SendGrid API
- **PDF Generation**: WeasyPrint
- **Hosting**: Railway
- **Task Queue**: Celery + Redis (for background tasks)

## Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL database
- SendGrid API key
- Redis (for background tasks)

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Run database migrations:
   ```bash
   alembic upgrade head
   ```

5. Start the application:
   ```bash
   uvicorn app.main:app --reload
   ```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

Create a `.env` file with the following variables:

```env
DATABASE_URL=postgresql://user:password@localhost/castle_reservations
SECRET_KEY=your-secret-key-here
SENDGRID_API_KEY=your-sendgrid-api-key
SENDGRID_FROM_EMAIL=noreply@thecastle.de
FRONTEND_URL=https://reservations.thecastle.de
```

## Project Structure

```
app/
├── api/                 # API routes
│   ├── admin/          # Admin endpoints
│   ├── public/         # Public API endpoints
│   └── auth/           # Authentication endpoints
├── core/               # Core configuration
├── models/             # Database models
├── schemas/            # Pydantic schemas
├── services/           # Business logic
├── utils/              # Utility functions
└── templates/          # Email templates
```

## Deployment

The system is designed to be deployed on Railway with built-in PostgreSQL support. See `railway.json` for deployment configuration.

## License

Private - The Castle Pub 