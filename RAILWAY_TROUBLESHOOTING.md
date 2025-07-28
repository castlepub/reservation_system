# Railway Deployment Troubleshooting Guide

## 🚨 Common Issues and Solutions

### 1. Health Check Failures

**Problem**: Railway health check fails with "service unavailable"

**Solutions**:
- ✅ **Health endpoint exists**: `/health` endpoint is implemented
- ✅ **Database connection**: Health check now tests database connectivity
- ✅ **Startup time**: Increased timeout to 300 seconds
- ✅ **Proper startup**: Using dedicated startup script

**Debug Steps**:
1. Check Railway logs for startup errors
2. Verify environment variables are set
3. Test health endpoint manually: `curl https://your-app.railway.app/health`

### 2. PostgreSQL Database Missing

**Problem**: No PostgreSQL service added to Railway project

**Solution**:
1. Go to Railway project dashboard
2. Click **"New Service"**
3. Select **"Database"** → **"PostgreSQL"**
4. Railway will automatically provision and connect the database

**Required Variables**:
```env
DATABASE_URL=postgresql://...  # Auto-provided by Railway after adding PostgreSQL
SECRET_KEY=your-secret-key     # Must be set manually
ALGORITHM=HS256               # Optional, defaults to HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30 # Optional, defaults to 30
```

### 3. Environment Variables Missing

**How to Set**:
1. Go to Railway Dashboard
2. Select your project
3. Go to "Variables" tab
4. Add the required variables

### 4. Database Connection Issues

**Common Causes**:
- PostgreSQL service not added to Railway project
- Wrong DATABASE_URL format
- Network connectivity issues

**Solutions**:
- ✅ Add PostgreSQL service to Railway project
- ✅ Railway automatically provides DATABASE_URL
- ✅ Database tables are created on startup
- ✅ Connection is tested during health check

### 5. Application Startup Failures

**Debug Steps**:
1. Check Railway logs for Python errors
2. Verify all dependencies are in `requirements.txt`
3. Ensure startup script is executable

**Common Fixes**:
- ✅ Using `start_railway.py` for proper initialization
- ✅ All dependencies listed in `requirements.txt`
- ✅ Proper error handling and logging

## 🔧 Manual Testing

### Test PostgreSQL Setup
```bash
# Check if PostgreSQL is properly configured
python setup_railway_postgres.py
```

### Test Health Check Locally
```bash
# Start the application
python start_railway.py

# In another terminal, test health check
python test_health.py

# Or test with curl
curl http://localhost:8000/health
```

### Test Health Check on Railway
```bash
# Replace with your Railway URL
curl https://your-app-name.railway.app/health
```

## 📋 Deployment Checklist

### Before Deploying
- [ ] All environment variables set in Railway
- [ ] `requirements.txt` includes all dependencies
- [ ] `railway.json` configured correctly
- [ ] Health check endpoint implemented
- [ ] Database models are correct

### After Deploying
- [ ] Check Railway logs for errors
- [ ] Test health endpoint manually
- [ ] Verify database connection
- [ ] Test main application endpoints

## 🚀 Quick Fix Commands

### Reset Railway Deployment
```bash
# In Railway CLI
railway up --detach
```

### Check Railway Logs
```bash
# In Railway CLI
railway logs
```

### Test Health Check
```bash
# Replace with your app URL
curl https://your-app.railway.app/health
```

## 📞 Getting Help

If you're still having issues:

1. **Check Railway Logs**: Look for specific error messages
2. **Test Locally**: Run `python start_railway.py` locally first
3. **Verify Environment**: Ensure all required variables are set
4. **Check Dependencies**: Make sure all packages are in `requirements.txt`

## 🔍 Debug Mode

To enable debug mode, add this environment variable:
```env
DEBUG=true
```

This will provide more detailed logging in the Railway console.

## 📊 Health Check Response

Expected response from `/health`:
```json
{
  "status": "healthy",
  "service": "reservation-system",
  "database": "connected",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

If you see an error response, check the Railway logs for the specific error message. 