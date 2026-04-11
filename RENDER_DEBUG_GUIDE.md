# Render Deployment Debug Guide

## Current Status
Your Telegram bot was showing specific database errors. We've fixed the phone field length issue, but let's troubleshoot any remaining problems.

## Immediate Steps

### 1. Check Render Logs
Go to your Render dashboard → Your service → **Logs tab**
Look for:
- Recent error messages
- Stack traces
- Database connection issues
- Bot startup problems

### 2. Run Database Migration (if needed)
If you're still seeing database errors, run the migration:

```bash
# In Render dashboard, go to your service → Shell tab
python migrations/update_phone_field_length.py
```

### 3. Test Bot Token
Verify your bot token is working:
```bash
curl -X POST "https://api.telegram.org/bot7671092916:AAG4GMyeTli6V9rEF6GH9H_HliV4QRq8Guw/getMe"
```

### 4. Check Environment Variables
Ensure these are set in Render dashboard:

**Required:**
- `DATABASE_URL`: `postgresql://neondb_owner:npg_vVJ1xS3CwXIf@ep-small-tree-anl3swp3-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require`
- `TELEGRAM_BOT_TOKEN`: `7671092916:AAG4GMyeTli6V9rEF6GH9H_HliV4QRq8Guw`
- `FLASK_ENV`: `production`

**Optional:**
- `PUBLIC_BASE_URL`: `https://college-virtual-assistant.onrender.com`

## Common Issues & Solutions

### Issue 1: Database Connection Errors
**Symptoms**: "Database connection failed", "Connection timeout"
**Solution**: Check Neon database status and connection string

### Issue 2: Bot Token Issues
**Symptoms**: "403 Forbidden", "Invalid bot token"
**Solution**: Verify token with @BotFather in Telegram

### Issue 3: Rate Limiting
**Symptoms**: "429 Too Many Requests"
**Solution**: Bot is being rate-limited, wait a few minutes

### Issue 4: Application Startup Errors
**Symptoms**: "Application failed to start", "Import errors"
**Solution**: Check for syntax errors in recent code changes

## Debug Commands

### Test Bot Directly
```bash
# Test bot functionality
curl -X POST "https://api.telegram.org/bot7671092916:AAG4GMyeTli6V9rEF6GH9H_HliV4QRq8Guw/getUpdates"
```

### Check Database Connection
```bash
# Test Neon database connection
python -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://neondb_owner:npg_vVJ1xS3CwXIf@ep-small-tree-anl3swp3-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require')
    print('✅ Database connection successful')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"
```

## Manual Restart Steps

1. **Go to Render Dashboard**
2. **Select your service**
3. **Click "Manual Deploy"**
4. **Click "Deploy Latest Commit"**

## What We Fixed So Far

✅ **Phone Field Length**: Increased from 15 to 20 characters
✅ **Error Handling**: Better specific error messages
✅ **Indentation Issues**: Fixed syntax errors
✅ **Environment Variables**: Manual setup guide

## Next Steps

1. **Check current logs** for specific error messages
2. **Run migration** if database schema issues persist
3. **Test bot token** if authentication errors occur
4. **Restart service** after any changes

## Contact Support

If issues persist:
- **Render Support**: Through Render dashboard
- **Neon Support**: Check database status
- **Telegram BotFather**: Verify bot token validity

---

**Your bot should now work properly with the phone field fix!** 🎯
