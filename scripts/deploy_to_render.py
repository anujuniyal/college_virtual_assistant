#!/usr/bin/env python3
"""
Render Deployment Script
Automates deployment to Render with Supabase database migration
"""

import os
import sys
import subprocess
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RenderDeployment:
    def __init__(self):
        self.project_root = os.getcwd()
        self.supabase_url = os.environ.get('DATABASE_URL')
        
        if not self.supabase_url:
            print("❌ DATABASE_URL environment variable not set")
            print("Please set your Supabase database URL in .env file")
            sys.exit(1)
    
    def check_prerequisites(self):
        """Check if all prerequisites are met"""
        print("🔍 Checking prerequisites...")
        
        # Check if required files exist
        required_files = [
            'render.yaml',
            'wsgi.py',
            'data/requirements.txt',
            'scripts/setup_supabase.py',
            'scripts/migrate_to_supabase.py',
            'app/factory.py'
        ]
        
        missing_files = []
        for file in required_files:
            if not os.path.exists(file):
                missing_files.append(file)
        
        if missing_files:
            print(f"❌ Missing required files: {', '.join(missing_files)}")
            return False
        
        # Check if render CLI is installed
        try:
            subprocess.run(['render', '--version'], capture_output=True, check=True)
            print("   ✅ Render CLI is installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("   ⚠️  Render CLI not found. Install it with: npm install -g render-cli")
            print("   ℹ️  You can also deploy manually through the Render dashboard")
            return False
        
        # Check if git repository is initialized
        if not os.path.exists('.git'):
            print("   ⚠️  Git repository not initialized")
            try:
                subprocess.run(['git', 'init'], check=True, capture_output=True)
                subprocess.run(['git', 'add', '.'], check=True, capture_output=True)
                subprocess.run(['git', 'commit', '-m', 'Initial commit for Render deployment'], check=True, capture_output=True)
                print("   ✅ Git repository initialized")
            except subprocess.CalledProcessError:
                print("   ❌ Failed to initialize git repository")
                return False
        else:
            print("   ✅ Git repository exists")
        
        print("   ✅ All prerequisites checked")
        return True
    
    def setup_supabase(self):
        """Setup Supabase database"""
        print("🏗️  Setting up Supabase database...")
        
        try:
            result = subprocess.run([
                'python', 'scripts/setup_supabase.py', 'full'
            ], capture_output=True, text=True, check=True)
            print("   ✅ Supabase setup completed")
            return True
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Supabase setup failed: {e.stderr}")
            return False
    
    def migrate_data(self):
        """Migrate data from SQLite to Supabase"""
        print("📊 Migrating data to Supabase...")
        
        try:
            result = subprocess.run([
                'python', 'scripts/migrate_to_supabase.py', 'full'
            ], capture_output=True, text=True, check=True)
            print("   ✅ Data migration completed")
            return True
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Data migration failed: {e.stderr}")
            return False
    
    def deploy_to_render(self):
        """Deploy to Render"""
        print("🚀 Deploying to Render...")
        
        try:
            # Deploy using render.yaml
            result = subprocess.run([
                'render', 'deploy'
            ], capture_output=True, text=True, check=True)
            print("   ✅ Deployment initiated")
            print("   📊 Check your Render dashboard for deployment status")
            return True
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Deployment failed: {e.stderr}")
            return False
    
    def create_deployment_guide(self):
        """Create deployment guide"""
        guide_content = """# Render Deployment Guide

## Prerequisites
1. **Render Account**: Create account at https://render.com
2. **Render CLI**: Install with `npm install -g render-cli`
3. **Supabase Database**: Set up Supabase project and get DATABASE_URL
4. **Git Repository**: Initialize git repository

## Environment Variables
Set these in your `.env` file:
```bash
DATABASE_URL=postgresql://postgres:password@db.supabase.co:5432/postgres
SECRET_KEY=your-secret-key-here
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
```

## Deployment Steps

### Option 1: Automated Deployment
```bash
# Run the deployment script
python scripts/deploy_to_render.py
```

### Option 2: Manual Deployment

1. **Setup Supabase Database**:
```bash
python scripts/setup_supabase.py setup
```

2. **Migrate Data** (if you have existing SQLite data):
```bash
python scripts/migrate_to_supabase.py migrate
```

3. **Deploy to Render**:
```bash
# Push to GitHub/GitLab first
git add .
git commit -m "Ready for Render deployment"
git push origin main

# Then deploy through Render dashboard or CLI
render deploy
```

## Post-Deployment Configuration

1. **Update Environment Variables in Render**:
   - Go to your Render service dashboard
   - Add sensitive environment variables (EMAIL, TELEGRAM_TOKEN, etc.)
   - Update SECRET_KEY if needed

2. **Verify Deployment**:
   - Check health endpoint: `https://your-app.onrender.com/health`
   - Test admin login
   - Verify database connectivity

3. **Set Up Custom Domain** (optional):
   - Add custom domain in Render dashboard
   - Update DNS records
   - Configure SSL certificate

## Monitoring and Maintenance

1. **Logs**: Check Render logs for any issues
2. **Database**: Monitor Supabase database usage
3. **Backups**: Enable automatic backups in Supabase
4. **Updates**: Regularly update dependencies

## Troubleshooting

### Common Issues:
1. **Database Connection**: Ensure DATABASE_URL is correct
2. **Build Failures**: Check requirements.txt and Python version
3. **Runtime Errors**: Check application logs
4. **Permission Issues**: Verify file permissions

### Health Check:
Your app includes a health check endpoint at `/health` that monitors:
- Database connectivity
- Application status
- Service availability

## Real-time Features

The application supports real-time updates:
- **Admin Dashboard**: Real-time activity refresh
- **Notifications**: Live notification updates
- **Bot Status**: Real-time bot monitoring
- **Database Sync**: Automatic data synchronization

## Security Considerations

1. **Environment Variables**: Never commit sensitive data to git
2. **HTTPS**: Render provides automatic SSL certificates
3. **Database Security**: Use Supabase Row Level Security (RLS)
4. **Session Security**: Secure cookies are enabled in production

## Scaling

When you need to scale:
1. **Render**: Upgrade to paid plan for better performance
2. **Database**: Upgrade Supabase plan for higher limits
3. **CDN**: Consider CDN for static assets
4. **Monitoring**: Set up application monitoring

## Support

- **Render Documentation**: https://render.com/docs
- **Supabase Documentation**: https://supabase.com/docs
- **Application Issues**: Check logs and contact support
"""
        
        with open('DEPLOYMENT_GUIDE.md', 'w') as f:
            f.write(guide_content)
        
        print("   📖 Deployment guide created: DEPLOYMENT_GUIDE.md")
    
    def run_deployment(self):
        """Run complete deployment process"""
        print("🚀 Starting Render deployment process...")
        print("=" * 60)
        
        # Check prerequisites
        if not self.check_prerequisites():
            print("❌ Prerequisites not met. Please fix issues and try again.")
            return False
        
        # Setup Supabase
        if not self.setup_supabase():
            print("❌ Supabase setup failed. Deployment aborted.")
            return False
        
        # Migrate data (optional - only if SQLite data exists)
        if os.path.exists('instance/edubot_management.db'):
            print("📊 Found SQLite database. Migrating data...")
            if not self.migrate_data():
                print("⚠️  Data migration failed, but continuing with deployment...")
        
        # Deploy to Render
        if not self.deploy_to_render():
            print("❌ Deployment failed.")
            return False
        
        # Create deployment guide
        self.create_deployment_guide()
        
        print("=" * 60)
        print("✅ Deployment process completed successfully!")
        print("🎉 Your app should be available on Render soon!")
        print("📖 Check DEPLOYMENT_GUIDE.md for detailed instructions")
        print("🔍 Monitor deployment status in your Render dashboard")
        
        return True

def main():
    """Main deployment function"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        deployment = RenderDeployment()
        
        if command == "deploy":
            deployment.run_deployment()
        elif command == "setup":
            deployment.setup_supabase()
        elif command == "migrate":
            deployment.migrate_data()
        elif command == "check":
            deployment.check_prerequisites()
        else:
            print("Usage: python deploy_to_render.py [deploy|setup|migrate|check]")
    else:
        print("Render Deployment Tool")
        print("Usage: python deploy_to_render.py [deploy|setup|migrate|check]")
        print("")
        print("Commands:")
        print("  deploy  - Run complete deployment process")
        print("  setup   - Setup Supabase database only")
        print("  migrate - Migrate SQLite data to Supabase")
        print("  check   - Check deployment prerequisites")

if __name__ == "__main__":
    main()
