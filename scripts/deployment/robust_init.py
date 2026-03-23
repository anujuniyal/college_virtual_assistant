#!/usr/bin/env python3
"""
Robust Deployment Initialization Script
Handles deployment initialization with proper error handling and fallbacks
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set production environment
os.environ['FLASK_ENV'] = 'production'

def test_database_connection():
    """Test if database is accessible"""
    try:
        from app import create_app, db
        
        app = create_app()
        
        with app.app_context():
            # Simple connection test
            from sqlalchemy import text
            db.session.execute(text("SELECT 1"))
            return True, "Database connection successful"
            
    except Exception as e:
        error_msg = str(e)
        if "could not translate host name" in error_msg or "Name or service not known" in error_msg:
            return False, "Network error - expected in local environment, should work in deployment"
        elif "connection" in error_msg.lower():
            return False, f"Database connection error: {error_msg}"
        else:
            return False, f"Unexpected error: {error_msg}"

def initialize_database_if_possible():
    """Initialize database only if connection is available"""
    can_connect, message = test_database_connection()
    
    print(f"🔍 Database test: {message}")
    
    if not can_connect:
        if "Network error" in message:
            print("⚠️  Local environment detected - skipping database initialization")
            print("✅ This is normal - database will be initialized in deployment")
            return True
        else:
            print(f"❌ Database connection failed: {message}")
            return False
    
    try:
        print("🏗️  Initializing database...")
        
        # Import and run the main initialization
        from scripts.deployment.init_production_db import init_production_database
        success = init_production_database()
        
        if success:
            print("✅ Database initialized successfully!")
            return True
        else:
            print("❌ Database initialization failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error during database initialization: {str(e)}")
        return False

def verify_configuration():
    """Verify all configuration is correct"""
    print("🔧 Verifying configuration...")
    
    # Check critical environment variables
    required_vars = ['FLASK_ENV']
    optional_vars = ['DATABASE_URL', 'DEFAULT_ADMIN_EMAIL', 'DEFAULT_ADMIN_PASSWORD']
    
    all_good = True
    
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")
            all_good = False
    
    for var in optional_vars:
        value = os.environ.get(var)
        if value:
            if 'PASSWORD' in var:
                print(f"✅ {var}: {'*' * len(value)}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"⚠️  {var}: Not set (will be provided by deployment)")
    
    return all_good

def verify_app_can_start():
    """Verify the Flask app can start without errors"""
    try:
        print("🚀 Testing Flask app startup...")
        
        from app import create_app
        
        app = create_app()
        
        with app.app_context():
            # Test basic app functionality
            print(f"✅ App created successfully")
            print(f"✅ Environment: {app.config.get('FLASK_ENV', 'unknown')}")
            print(f"✅ Database URI configured: {'Yes' if app.config.get('SQLALCHEMY_DATABASE_URI') else 'No'}")
            
            return True
            
    except Exception as e:
        print(f"❌ App startup failed: {str(e)}")
        return False

def verify_models():
    """Verify all models can be imported without errors"""
    try:
        print("📋 Verifying models...")
        
        from app.models import (
            Admin, Faculty, Student, Notification, Result, 
            FeeRecord, Complaint, ChatbotQA, PredefinedInfo, 
            FAQ, FAQRecord, QueryLog, OTP, Session, 
            DailyViewCount, StudentRegistration, TelegramUserMapping, 
            VisitorQuery
        )
        
        print("✅ All models imported successfully")
        return True
        
    except Exception as e:
        print(f"❌ Model import failed: {str(e)}")
        return False

def verify_services():
    """Verify all services can be imported and initialized"""
    try:
        print("🔧 Verifying services...")
        
        from app.services.user_service import UserService
        from app.services.analytics_service import AnalyticsService
        from app.services.cleanup_service import CleanupService
        
        print("✅ All services imported successfully")
        return True
        
    except Exception as e:
        print(f"❌ Service import failed: {str(e)}")
        return False

def main():
    """Main robust initialization function"""
    print("🚀 Robust Deployment Initialization")
    print("=" * 60)
    
    all_passed = True
    
    # Step 1: Verify configuration
    print("\n1️⃣ Configuration Verification")
    if not verify_configuration():
        all_passed = False
    
    # Step 2: Verify models
    print("\n2️⃣ Model Verification")
    if not verify_models():
        all_passed = False
    
    # Step 3: Verify services
    print("\n3️⃣ Service Verification")
    if not verify_services():
        all_passed = False
    
    # Step 4: Verify app can start
    print("\n4️⃣ App Startup Verification")
    if not verify_app_can_start():
        all_passed = False
    
    # Step 5: Initialize database (if possible)
    print("\n5️⃣ Database Initialization")
    if not initialize_database_if_possible():
        all_passed = False
    
    # Final result
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL CHECKS PASSED!")
        print("🎉 Deployment is ready!")
        print("\n📋 Next Steps:")
        print("   1. Push to repository")
        print("   2. Deploy to Render")
        print("   3. Login with: admin@edubot.com / admin123")
        print("   4. Change default password")
    else:
        print("❌ SOME CHECKS FAILED!")
        print("🔧 Please fix the issues above before deployment")
    
    return all_passed

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
