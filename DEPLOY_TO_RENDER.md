# Deploy to Render with Neon Database

This guide will help you deploy your college virtual assistant to Render using the Neon database.

## Prerequisites

1. **Render Account**: Create a free account at [https://render.com](https://render.com)
2. **GitHub Repository**: Your code should be pushed to a GitHub repository
3. **Neon Database**: Already configured and working

## Step 1: Prepare Your Repository

### 1.1 Commit All Changes
```bash
git add .
git status
git commit -m "Configure for Render deployment with Neon database"
```

### 1.2 Push to GitHub
```bash
git push origin main
```

## Step 2: Create Render Web Service

### 2.1 Go to Render Dashboard
1. Log in to [https://render.com](https://render.com)
2. Click **"New +"** button
3. Select **"Web Service"**

### 2.2 Connect Repository
1. **Connect GitHub/GitLab repository**
2. Select your college virtual assistant repository
3. Click **"Connect"**

### 2.3 Configure Web Service
**Basic Settings:**
- **Name**: `college-virtual-assistant`
- **Region**: Choose nearest to your users
- **Branch**: `main`
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120 --max-requests 1000 --max-requests-jitter 100 --limit-request-line 4094 --limit-request-field-size 8190 --preload --worker-class sync wsgi:app`

**Instance Type:**
- **Free** (for testing) or **Starter** (for production)

## Step 3: Configure Environment Variables

Render will automatically use your `render.yaml` file, but you can also set environment variables manually:

### 3.1 Database Configuration
```
DATABASE_URL=postgresql://neondb_owner:npg_vVJ1xS3CwXIf@ep-small-tree-anl3swp3-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
POSTGRESQL_URL=postgresql://neondb_owner:npg_vVJ1xS3CwXIf@ep-small-tree-anl3swp3-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
NEON_DATABASE_URL=postgresql://neondb_owner:npg_vVJ1xS3CwXIf@ep-small-tree-anl3swp3-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
```

### 3.2 Flask Configuration
```
FLASK_ENV=production
SECRET_KEY=your-generated-secret-key-here
```

### 3.3 Admin Credentials
```
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_EMAIL=admin@edubot.com
DEFAULT_ADMIN_PASSWORD=your-secure-password-here
DEFAULT_ADMIN_ROLE=admin
```

### 3.4 Email Configuration (Optional)
```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-gmail@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-gmail@gmail.com
```

### 3.5 Telegram Configuration (Optional)
```
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
```

## Step 4: Deploy

### 4.1 Create Web Service
1. Click **"Create Web Service"**
2. Render will automatically:
   - Build your application
   - Install dependencies
   - Start the server
   - Run health checks

### 4.2 Monitor Deployment
1. Watch the **Logs** tab for progress
2. Wait for the **"Live"** status
3. Check the **"Events"** tab for any issues

## Step 5: Verify Deployment

### 5.1 Access Your Application
Your app will be available at: `https://college-virtual-assistant.onrender.com`

### 5.2 Test Functionality
1. **Health Check**: Visit `https://college-virtual-assistant.onrender.com/health`
2. **Admin Login**: Use your admin credentials
3. **Database Connection**: Check if data loads correctly

### 5.3 Check Logs
1. Go to the **Logs** tab
2. Look for: "EduBot Production Startup with Neon"
3. Verify no database connection errors

## Troubleshooting

### Common Issues

#### 1. Build Fails
- Check `requirements.txt` for correct dependencies
- Verify Python version compatibility
- Check logs for specific error messages

#### 2. Database Connection Fails
- Verify Neon connection string is correct
- Check if Neon database is active
- Ensure SSL settings are correct (`sslmode=require`)

#### 3. Application Won't Start
- Check `wsgi.py` file exists and is correct
- Verify Gunicorn start command
- Check for missing environment variables

#### 4. Health Check Fails
- Ensure `/health` endpoint exists
- Check if application is binding to correct port
- Verify firewall settings

### Debug Commands

#### Check Application Status
```bash
# In Render shell (if available)
python -c "from app import create_app; app = create_app(); print('App created successfully')"
```

#### Test Database Connection
```bash
python -c "
import psycopg2
conn = psycopg2.connect('postgresql://neondb_owner:npg_vVJ1xS3CwXIf@ep-small-tree-anl3swp3-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require')
print('Database connected successfully')
conn.close()
"
```

## Post-Deployment

### 1. Set Up Custom Domain (Optional)
1. Go to your web service settings
2. Click **"Custom Domain"**
3. Add your domain name
4. Configure DNS records

### 2. Set Up Monitoring
1. Enable Render's built-in monitoring
2. Set up alerts for downtime
3. Monitor database usage

### 3. Backup Strategy
1. Neon automatically backs up your database
2. Export important data regularly
3. Monitor storage limits

## Performance Optimization

### 1. Free Tier Limitations
- **Sleeps after 15 minutes** of inactivity
- **Cold starts** can take 30-60 seconds
- **Limited bandwidth** and memory

### 2. Upgrade Options
- **Starter Plan** ($7/month): No sleep, better performance
- **Standard Plan** ($25/month): More resources, faster startup

### 3. Optimization Tips
- Use connection pooling
- Optimize database queries
- Enable caching
- Minimize asset sizes

## Security Best Practices

1. **Environment Variables**: Never commit secrets to git
2. **Database Security**: Use SSL connections
3. **User Authentication**: Strong admin passwords
4. **HTTPS**: Render provides SSL automatically
5. **Regular Updates**: Keep dependencies updated

## Support

- **Render Docs**: [https://render.com/docs](https://render.com/docs)
- **Neon Docs**: [https://neon.tech/docs](https://neon.tech/docs)
- **Application Issues**: Check Render logs first

---

**Your application is now ready for deployment!** Follow these steps carefully and your college virtual assistant will be running on Render with Neon database in minutes.
