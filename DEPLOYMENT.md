# 🚀 Deployment Guide

## Railway Deployment (Recommended)

Railway is the easiest way to deploy your reservation system with automatic PostgreSQL database provisioning.

### Step 1: Connect to Railway

1. **Visit Railway**: https://railway.app
2. **Sign in** with your GitHub account
3. **Create a new project**
4. **Connect your repository**: `castlepub/reservation_system`

### Step 2: Configure Environment Variables

In your Railway project dashboard, add these environment variables:

```env
DATABASE_URL=postgresql://...  # Auto-provided by Railway
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
SENDGRID_API_KEY=your-sendgrid-api-key
SENDGRID_FROM_EMAIL=noreply@thecastle.de
FRONTEND_URL=https://your-app-name.railway.app
REDIS_URL=redis://...  # Optional, for background tasks
RESERVATION_TOKEN_EXPIRE_DAYS=30
MAX_PARTY_SIZE=20
MIN_RESERVATION_HOURS=2
MAX_RESERVATION_DAYS=90
OPENING_HOUR=11
CLOSING_HOUR=23
```

### Step 3: Deploy

1. **Railway will automatically detect** the Python project
2. **Install dependencies** from `requirements.txt`
3. **Run migrations** automatically
4. **Start the server** using the command in `railway.json`

### Step 4: Access Your App

- **Main Website**: `https://your-app-name.railway.app`
- **API Documentation**: `https://your-app-name.railway.app/docs`
- **Admin Login**: admin / admin123

## Manual Deployment

### Prerequisites

- Python 3.8+
- PostgreSQL database
- Domain name (optional)

### Step 1: Server Setup

```bash
# Clone the repository
git clone https://github.com/castlepub/reservation_system.git
cd reservation_system

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

### Step 2: Database Setup

```bash
# Run database migrations
alembic upgrade head

# Initialize with sample data
python scripts/init_db.py
```

### Step 3: Start the Server

```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production (with Gunicorn)
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Step 4: Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Docker Deployment

### Step 1: Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 2: Build and Run

```bash
# Build the image
docker build -t castle-reservation-system .

# Run with PostgreSQL
docker run -d \
  --name castle-reservation \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  castle-reservation-system
```

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `SECRET_KEY` | JWT secret key | `your-super-secret-key` |
| `ALGORITHM` | JWT algorithm | `HS256` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiry | `30` |
| `SENDGRID_API_KEY` | Email service API key | `None` |
| `SENDGRID_FROM_EMAIL` | From email address | `noreply@thecastle.de` |
| `FRONTEND_URL` | Frontend URL | `http://localhost:3000` |
| `MAX_PARTY_SIZE` | Maximum party size | `20` |
| `OPENING_HOUR` | Restaurant opening hour | `11` |
| `CLOSING_HOUR` | Restaurant closing hour | `23` |

## SSL/HTTPS Setup

### Railway (Automatic)
Railway automatically provides SSL certificates for your domain.

### Manual Setup (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Monitoring and Logs

### Railway
- **Logs**: Available in Railway dashboard
- **Metrics**: Automatic monitoring
- **Alerts**: Configure in dashboard

### Manual Setup

```bash
# View logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Monitor process
htop
ps aux | grep uvicorn
```

## Backup Strategy

### Database Backups

```bash
# PostgreSQL backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Restore
psql $DATABASE_URL < backup_20231201.sql
```

### File Backups

```bash
# Backup static files
tar -czf static_backup_$(date +%Y%m%d).tar.gz static/

# Backup configuration
cp .env .env.backup
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check `DATABASE_URL` format
   - Ensure database is running
   - Verify network connectivity

2. **Static Files Not Loading**
   - Check file permissions
   - Verify static directory exists
   - Clear browser cache

3. **Email Not Sending**
   - Verify SendGrid API key
   - Check email configuration
   - Review SendGrid logs

4. **Performance Issues**
   - Monitor database queries
   - Check server resources
   - Optimize static file serving

### Health Checks

```bash
# Check API health
curl https://your-domain.com/health

# Check database
python -c "from app.core.database import engine; print(engine.execute('SELECT 1').scalar())"

# Check static files
curl https://your-domain.com/static/test.html
```

## Security Checklist

- [ ] Change default admin password
- [ ] Use strong SECRET_KEY
- [ ] Enable HTTPS
- [ ] Set up firewall rules
- [ ] Regular security updates
- [ ] Database backups
- [ ] Monitor access logs
- [ ] Rate limiting enabled

## Support

For deployment issues:
1. Check the logs
2. Review environment variables
3. Test locally first
4. Create an issue in the repository 