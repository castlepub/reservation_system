# 🔧 Troubleshooting Guide

## Common Issues and Solutions

### 1. **JavaScript Error: "A listener indicated an asynchronous response by returning true, but the message channel closed before a response was received"**

This error is typically caused by:
- Browser extensions interfering with the page
- Service workers or background scripts
- Network connectivity issues

**Solutions:**
1. **Try Incognito/Private Mode**: Open the site in an incognito window
2. **Disable Browser Extensions**: Temporarily disable all browser extensions
3. **Clear Browser Cache**: Press `Ctrl + Shift + R` (force refresh)
4. **Check Console**: Press `F12` and look for other errors in the Console tab

### 2. **"No module named 'fastapi'" Error**

**Solution:**
```bash
python start_system.py
```
This script will automatically install all required dependencies.

### 3. **Server Won't Start**

**Solutions:**
1. **Check if port 8000 is in use**:
   ```bash
   netstat -ano | findstr :8000
   ```
2. **Kill any processes using port 8000**:
   ```bash
   taskkill /PID <PID> /F
   ```
3. **Try a different port**: Edit `start_system.py` and change port 8000 to 8001

### 4. **Static Files Not Loading**

**Solutions:**
1. **Check file paths**: Ensure `static/` directory exists with `index.html`, `styles.css`, `script.js`
2. **Clear browser cache**: Press `Ctrl + F5`
3. **Check browser console**: Press `F12` and look for 404 errors

### 5. **Database Connection Issues**

**Solutions:**
1. **SQLite file permissions**: Ensure the app can write to the current directory
2. **Database corruption**: Delete `castle_reservations.db` and restart
3. **Check local_config.py**: Ensure DATABASE_URL is set correctly

### 6. **Admin Login Not Working**

**Default credentials:**
- Username: `admin`
- Password: `admin123`

**If login fails:**
1. Check if the database was initialized
2. Run the initialization script: `python scripts/init_db.py`

### 7. **Reservation Form Not Working**

**Solutions:**
1. **Check server status**: Ensure the API is running
2. **Check browser console**: Look for network errors
3. **Test API directly**: Visit http://localhost:8000/docs

### 8. **Mobile/Responsive Issues**

**Solutions:**
1. **Check viewport meta tag**: Ensure it's present in index.html
2. **Test on different devices**: Try different screen sizes
3. **Check CSS media queries**: Ensure responsive design is working

## Quick Fix Commands

```bash
# Install dependencies
python start_system.py

# Check if server is running
curl http://localhost:8000/health

# Test static files
curl http://localhost:8000/static/test.html

# Initialize database
python scripts/init_db.py

# Restart server
python restart_server.py
```

## Browser-Specific Issues

### Chrome/Edge
- Clear cache: `Ctrl + Shift + Delete`
- Disable extensions: Go to `chrome://extensions/`
- Check console: `F12` → Console tab

### Firefox
- Clear cache: `Ctrl + Shift + Delete`
- Disable add-ons: Go to `about:addons`
- Check console: `F12` → Console tab

### Safari
- Clear cache: `Cmd + Option + E`
- Disable extensions: Safari → Preferences → Extensions
- Check console: `Cmd + Option + C`

## Network Issues

### CORS Errors
- The server includes CORS middleware
- If you see CORS errors, check the browser console
- Ensure you're accessing via `http://localhost:8000`

### Connection Refused
- Check if the server is running
- Ensure no firewall is blocking port 8000
- Try accessing `http://127.0.0.1:8000` instead of `localhost`

## Performance Issues

### Slow Loading
- Check browser network tab for slow requests
- Ensure static files are being served correctly
- Consider using a CDN for external resources

### Memory Issues
- Check if the database file is growing too large
- Restart the server periodically
- Monitor system resources

## Getting Help

If you're still having issues:

1. **Check the logs**: Look at the terminal output when starting the server
2. **Browser console**: Press `F12` and check for errors
3. **API documentation**: Visit http://localhost:8000/docs
4. **Test endpoints**: Use the test scripts provided

## Emergency Reset

If everything is broken:

```bash
# Stop the server (Ctrl+C)
# Delete database
del castle_reservations.db

# Reinstall dependencies
python install_deps.py

# Initialize database
python scripts/init_db.py

# Start server
python start_system.py
``` 