# Deploy EduBot College Assistant to Render

## 🚀 Quick Deployment Guide

### 1. Prepare Your Repository
- Push your code to GitHub
- Ensure all files are committed including `render.yaml`

### 2. Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Verify your email

### 3. Deploy Web Service
1. Click "New +" → "Web Service"
2. Connect your GitHub repository
3. Select the repository
4. Render will automatically detect `render.yaml`
5. Configure:
   - **Name**: edubot-college-assistant
   - **Environment**: Python 3
   - **Branch**: main
   - **Root Directory**: . (leave empty)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 120 wsgi:app`

### 4. Set Environment Variables
In Render Dashboard → your service → Environment:
```
FLASK_ENV=production
SECRET_KEY=your-unique-secret-key-here
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
TELEGRAM_BOT_TOKEN=7671092916:AAG4GMyeTli6V9rEF6GH9H_HliV4QRq8Guw
```

### 5. Deploy PostgreSQL Database
1. Click "New +" → "PostgreSQL"
2. **Name**: edubot-db
3. **Database Name**: edubot
4. **User**: edubot_user
5. Choose free plan
6. After creation, copy the connection string
7. Update `DATABASE_URL` in environment variables

### 6. Update Database URL
In your service environment variables:
```
DATABASE_URL=postgresql://edubot_user:password@host:5432/edubot
```
(Replace with actual credentials from Render dashboard)

### 7. Deploy and Test
1. Click "Create Web Service"
2. Wait for deployment (2-5 minutes)
3. Access your app at: `https://edubot-college-assistant.onrender.com`

### 8. Post-Deployment Setup
1. **Initialize Database**: Visit `/admin/dashboard` to create tables
2. **Test Bot**: Send message to your Telegram bot
3. **Update Webhook**: Set Telegram webhook to your Render URL

## 📱 Telegram Bot Setup
After deployment:
1. Update webhook: `https://edubot-college-assistant.onrender.com/webhook/telegram`
2. Test with: `@edubot_assistant_bot`

## 🔧 Troubleshooting

### Common Issues:
1. **Build Fails**: Check Python version in `render.yaml`
2. **Database Errors**: Verify `DATABASE_URL` format
3. **Bot Not Responding**: Check webhook URL and bot token
4. **500 Errors**: Check Render logs in dashboard

### Logs Location:
- Render Dashboard → your service → Logs
- Check for any import errors or database connection issues

## 🌐 Access URLs
- **Web App**: `https://edubot-college-assistant.onrender.com`
- **Admin**: `https://edubot-college-assistant.onrender.com/login`
- **Bot Webhook**: `https://edubot-college-assistant.onrender.com/webhook/telegram`

## 💡 Tips
- Use Render's free tier for testing
- Upgrade to paid plan for production
- Monitor logs regularly
- Set up custom domain if needed
