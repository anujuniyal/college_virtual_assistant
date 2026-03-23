#!/usr/bin/env python3
"""
Deployment Health Check Script
Diagnoses issues in the deployed application
"""

import os
import sys
import requests
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def check_app_health(base_url="https://college-virtual-assistant.onrender.com"):
    """Check if the deployed app is responding"""
    try:
        print("🔍 Checking application health...")
        
        # Check main page
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            print("✅ Main page accessible")
        else:
            print(f"❌ Main page error: {response.status_code}")
            return False
        
        # Check login page
        response = requests.get(f"{base_url}/auth/login", timeout=10)
        if response.status_code == 200:
            print("✅ Login page accessible")
        else:
            print(f"❌ Login page error: {response.status_code}")
            return False
        
        # Check health endpoint if exists
        try:
            response = requests.get(f"{base_url}/health", timeout=10)
            if response.status_code == 200:
                print("✅ Health endpoint responding")
                print(f"   Health data: {response.text[:100]}...")
        except:
            print("⚠️  Health endpoint not available")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Application health check failed: {str(e)}")
        return False

def test_authentication_endpoint(base_url="https://college-virtual-assistant.onrender.com"):
    """Test the authentication endpoint directly"""
    try:
        print("\n🔐 Testing authentication endpoint...")
        
        # Test login with correct credentials
        session = requests.Session()
        
        # Get login page first (to get cookies)
        login_page = session.get(f"{base_url}/auth/login", timeout=10)
        
        # Test POST request
        login_data = {
            'username': 'admin@edubot.com',
            'password': 'admin123',
            'selected_role': 'admin'
        }
        
        response = session.post(f"{base_url}/auth/login", data=login_data, timeout=10, allow_redirects=False)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 302:
            # Check redirect location
            redirect_url = response.headers.get('Location', '')
            print(f"   Redirect: {redirect_url}")
            
            if 'dashboard' in redirect_url or 'admin' in redirect_url:
                print("✅ Authentication successful - redirecting to dashboard")
                return True
            else:
                print("⚠️  Authentication redirected but not to dashboard")
        elif response.status_code == 200:
            # Check if login page shows error
            if 'Authentication failed' in response.text:
                print("❌ Authentication failed - credentials rejected")
            else:
                print("⚠️  Authentication returned login page without error message")
        else:
            print(f"❌ Unexpected authentication response: {response.status_code}")
        
        return False
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Authentication test failed: {str(e)}")
        return False

def check_database_status():
    """Check database connection status"""
    try:
        print("\n🗄️  Checking database configuration...")
        
        # Set production environment
        os.environ['FLASK_ENV'] = 'production'
        
        from app import create_app, db
        from app.models import Admin, Faculty
        
        app = create_app()
        
        with app.app_context():
            # Test database connection
            try:
                from sqlalchemy import text
                result = db.session.execute(text("SELECT 1"))
                print("✅ Database connection successful")
            except Exception as e:
                print(f"❌ Database connection failed: {str(e)}")
                return False
            
            # Check if admin users exist
            try:
                admin_count = Admin.query.count()
                faculty_count = Faculty.query.count()
                
                print(f"📊 Admin users: {admin_count}")
                print(f"📊 Faculty users: {faculty_count}")
                
                if admin_count == 0 and faculty_count == 0:
                    print("❌ No users found in database")
                    return False
                
                # Check specific admin user
                admin_user = Admin.query.filter_by(email='admin@edubot.com').first()
                if admin_user:
                    print("✅ Default admin user found")
                    print(f"   Email: {admin_user.email}")
                    print(f"   Role: {admin_user.role}")
                    print(f"   Active: {admin_user.is_active}")
                else:
                    print("❌ Default admin user not found")
                    
                    # Check faculty table
                    faculty_user = Faculty.query.filter_by(email='admin@edubot.com').first()
                    if faculty_user:
                        print("✅ Admin user found in Faculty table")
                        print(f"   Email: {faculty_user.email}")
                        print(f"   Role: {faculty_user.role}")
                    else:
                        print("❌ Admin user not found in either table")
                        return False
                
            except Exception as e:
                print(f"❌ User query failed: {str(e)}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Database check failed: {str(e)}")
        return False

def diagnose_authentication_issue():
    """Diagnose why authentication is failing"""
    try:
        print("\n🔍 Diagnosing authentication issue...")
        
        os.environ['FLASK_ENV'] = 'production'
        
        from app import create_app
        from app.services.user_service import UserService
        
        app = create_app()
        
        with app.app_context():
            # Test authentication directly
            print("   Testing UserService.authenticate_user()...")
            
            result = UserService.authenticate_user('admin@edubot.com', 'admin123')
            
            print(f"   Success: {result['success']}")
            print(f"   Message: {result['message']}")
            
            if result['success']:
                print(f"   User: {result['user']}")
                print(f"   User Type: {type(result['user']).__name__}")
                return True
            else:
                print("❌ Direct authentication test failed")
                
                # Let's check what users actually exist
                from app.models import Admin, Faculty
                
                print("\n   Checking existing users...")
                
                admins = Admin.query.all()
                print(f"   Admin table has {len(admins)} users:")
                for admin in admins:
                    print(f"     - {admin.email} ({admin.role})")
                
                faculty = Faculty.query.all()
                print(f"   Faculty table has {len(faculty)} users:")
                for f in faculty:
                    print(f"     - {f.email} ({f.role})")
                
                return False
        
    except Exception as e:
        print(f"❌ Authentication diagnosis failed: {str(e)}")
        return False

def main():
    """Main health check function"""
    print("🚀 Deployment Health Check")
    print("=" * 60)
    print("URL: https://college-virtual-assistant.onrender.com")
    print("=" * 60)
    
    all_good = True
    
    # 1. Check application health
    if not check_app_health():
        all_good = False
    
    # 2. Test authentication endpoint
    if not test_authentication_endpoint():
        all_good = False
    
    # 3. Check database status
    if not check_database_status():
        all_good = False
    
    # 4. Diagnose authentication issue
    if not diagnose_authentication_issue():
        all_good = False
    
    print("\n" + "=" * 60)
    if all_good:
        print("✅ ALL CHECKS PASSED!")
        print("🎉 Deployment is healthy!")
    else:
        print("❌ SOME CHECKS FAILED!")
        print("🔧 Issues found that need to be addressed")
    
    return all_good

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
