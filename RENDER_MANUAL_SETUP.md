# Manual Render Environment Setup

Since the YAML configuration isn't working properly, let's set environment variables manually in the Render dashboard.

## Step 1: Go to Render Dashboard

1. Go to your Render dashboard
2. Click on your `college-virtual-assistant` service
3. Go to the **"Environment"** tab

## Step 2: Add Environment Variables

Add these environment variables one by one:

### Database Configuration
- **DATABASE_URL**: `postgresql://neondb_owner:npg_vVJ1xS3CwXIf@ep-small-tree-anl3swp3-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require`
- **POSTGRESQL_URL**: `postgresql://neondb_owner:npg_vVJ1xS3CwXIf@ep-small-tree-anl3swp3-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require`
- **NEON_DATABASE_URL**: `postgresql://neondb_owner:npg_vVJ1xS3CwXIf@ep-small-tree-anl3swp3-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require`

### Flask Configuration
- **FLASK_ENV**: `production`

### Admin Credentials
- **DEFAULT_ADMIN_USERNAME**: `admin`
- **DEFAULT_ADMIN_EMAIL**: `admin@edubot.com`
- **DEFAULT_ADMIN_PASSWORD**: `admin123`
- **DEFAULT_ADMIN_ROLE**: `admin`
- **ADMIN_EMAIL**: `admin@edubot.com`

### Optional Variables (if needed)
- **MAIL_SERVER**: `smtp.gmail.com`
- **MAIL_PORT**: `587`
- **MAIL_USE_TLS**: `true`
- **TELEGRAM_BOT_TOKEN**: `[your-bot-token]`
- **PUBLIC_BASE_URL**: `https://college-virtual-assistant.onrender.com`

## Step 3: Update Start Command

In the Render dashboard, update the start command to:
```
gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120 --max-requests 1000 --max-requests-jitter 100 --limit-request-line 4094 --limit-request-field-size 8190 --preload --worker-class sync wsgi:app
```

## Step 4: Redeploy

1. Click **"Manual Deploy"** in Render dashboard
2. Click **"Deploy Latest Commit"**
3. Wait for deployment to complete

## Step 5: Verify

Check the logs to see:
- ✅ No more "No DATABASE_URL found" warnings
- ✅ "EduBot Production Startup with Neon" message
- ✅ No SQLite database errors
- ✅ Application connects to Neon successfully

## Expected Results

After manual setup:
- **URL**: `https://college-virtual-assistant.onrender.com`
- **Health Check**: `/health` endpoint works
- **Admin Login**: `admin` / `admin123`
- **Database**: Connected to Neon (not SQLite)

## Troubleshooting

If still issues:
1. **Check Render logs** for exact error messages
2. **Verify Neon database** is active and accessible
3. **Test connection** locally with same environment variables
4. **Contact Render support** if dashboard issues

This manual approach bypasses the YAML configuration issues and ensures environment variables are set correctly.
