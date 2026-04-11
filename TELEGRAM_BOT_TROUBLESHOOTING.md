# Telegram Bot Troubleshooting Guide

## Error: "I'm experiencing technical difficulties. Please try again later."

This error typically indicates one of the following issues:

## 1. Bot Token Issues

### Check Token Validity
- Verify your bot token is correct: `7671092916:AAG4GMyeTli6V9rEF6GH9H_HliV4QRq8Guw`
- Make sure bot is still active in Telegram
- Check if token has been revoked

### Test Token Locally
```bash
curl -X POST "https://api.telegram.org/bot7671092916:AAG4GMyeTli6V9rEF6GH9H_HliV4QRq8Guw/getMe"
```

## 2. Network/Connection Issues

### Check Render Network
- Render might be blocking outgoing connections
- Check if Telegram API is accessible from Render

### Test Connection from Render
Add this to your Render environment variables temporarily:
- **TELEGRAM_DEBUG**: `true`

## 3. Rate Limiting

### Telegram API Limits
- Too many requests in short time
- Bot might be rate-limited
- Wait a few minutes before retrying

## 4. Code Issues

### Check Bot Script
The error might be in `/app/scripts/bot/run_telegram_bot_polling.py`

### Common Issues:
- Exception handling not catching all errors
- Network timeout issues
- Invalid API calls
- Missing error recovery

## 5. Environment Variable Issues

### Verify All Required Variables
Make sure these are set in Render:
- **TELEGRAM_BOT_TOKEN**: `7671092916:AAG4GMyeTli6V9rEF6GH9H_HliV4QRq8Guw`
- **PUBLIC_BASE_URL**: `https://college-virtual-assistant.onrender.com`
- **FLASK_ENV**: `production`

## Immediate Actions

### 1. Check Render Logs
Go to Render dashboard → Your service → Logs tab
Look for:
- Specific error messages
- Stack traces
- Network errors

### 2. Restart Bot
In Render dashboard:
- Go to Manual Deploy
- Click "Deploy Latest Commit"
- This will restart the bot

### 3. Test Manually
Try sending a simple message to the bot:
- `/start`
- `/help`
- Simple text message

## Debugging Steps

### Step 1: Enable Debug Mode
Add to Render environment:
- **DEBUG**: `true`
- **TELEGRAM_DEBUG**: `true`

### Step 2: Check Bot Status
Visit: `https://api.telegram.org/bot7671092916:AAG4GMyeTli6V9rEF6GH9H_HliV4QRq8Guw/getMe`

### Step 3: Test Webhook vs Polling
The bot might be using polling (as seen in logs):
- `Student/Visitor Bot (Polling) mode`

## Common Solutions

### Solution 1: Restart Service
```
In Render Dashboard:
1. Go to your service
2. Click "Manual Deploy"
3. Click "Deploy Latest Commit"
```

### Solution 2: Check Token
```
1. Go to @BotFather in Telegram
2. Check if your bot is still active
3. Get a new token if needed
4. Update TELEGRAM_BOT_TOKEN in Render
```

### Solution 3: Add Error Handling
If you have access to the bot script, add better error handling:
```python
try:
    # Bot code here
except Exception as e:
    logger.error(f"Bot error: {e}")
    # Send error message to user
```

## When to Contact Support

- If the issue persists after restarting
- If you see specific error codes in logs
- If the bot token is confirmed valid
- If network tests fail

## Next Steps

1. **Check Render logs** for specific error details
2. **Try restarting** the service
3. **Test bot token** validity
4. **Report back** with specific error messages from logs

The "technical difficulties" message is usually a catch-all error that needs investigation through logs.
