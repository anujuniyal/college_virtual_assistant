#!/usr/bin/env python3
"""
Debug authentication endpoint
Tests the login endpoint to identify 500 error causes
"""

import os
import sys
import requests
from urllib.parse import urljoin

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def test_login_endpoint():
    """Test login endpoint locally"""
    try:
        from app import create_app
        from app.services.user_service import UserService
        
        print("🔍 Testing Login Endpoint Locally")
        print("=" * 50)
        
        app = create_app()
        
        with app.test_client() as client:
            print("✅ Test client created")
            
            # Test GET request to login page
            print("\n1️⃣ Testing GET /auth/login:")
            try:
                response = client.get('/auth/login')
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    print("✅ GET login page: SUCCESS")
                else:
                    print(f"❌ GET login page: FAILED - {response.status_code}")
                    print(f"   Response: {response.data.decode()}")
                    return False
            except Exception as e:
                print(f"❌ GET login page: ERROR - {str(e)}")
                return False
            
            # Test POST request with valid credentials
            print("\n2️⃣ Testing POST /auth/login (valid credentials):")
            try:
                response = client.post('/auth/login', data={
                    'username': 'admin@edubot.com',
                    'password': 'admin123'
                }, follow_redirects=False)
                print(f"   Status: {response.status_code}")
                if response.status_code in [302, 200]:
                    print("✅ POST login (valid): SUCCESS")
                    if response.status_code == 302:
                        print(f"   Redirect to: {response.location}")
                else:
                    print(f"❌ POST login (valid): FAILED - {response.status_code}")
                    print(f"   Response: {response.data.decode()}")
                    return False
            except Exception as e:
                print(f"❌ POST login (valid): ERROR - {str(e)}")
                import traceback
                traceback.print_exc()
                return False
            
            # Test POST request with invalid credentials
            print("\n3️⃣ Testing POST /auth/login (invalid credentials):")
            try:
                response = client.post('/auth/login', data={
                    'username': 'admin@edubot.com',
                    'password': 'wrongpassword'
                }, follow_redirects=False)
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    print("✅ POST login (invalid): SUCCESS (shows login page with error)")
                else:
                    print(f"❌ POST login (invalid): FAILED - {response.status_code}")
                    print(f"   Response: {response.data.decode()}")
                    return False
            except Exception as e:
                print(f"❌ POST login (invalid): ERROR - {str(e)}")
                return False
            
            # Test UserService directly
            print("\n4️⃣ Testing UserService directly:")
            try:
                with app.app_context():
                    result = UserService.authenticate_user('admin@edubot.com', 'admin123')
                    if result['success']:
                        print("✅ UserService authentication: SUCCESS")
                        print(f"   User: {result['user'].name} ({result['user'].role})")
                    else:
                        print(f"❌ UserService authentication: FAILED - {result['message']}")
                        return False
            except Exception as e:
                print(f"❌ UserService authentication: ERROR - {str(e)}")
                import traceback
                traceback.print_exc()
                return False
            
            print("\n" + "=" * 50)
            print("🎉 All local tests passed!")
            print("\n📋 If local tests pass but deployment fails, check:")
            print("1. Environment variables in production")
            print("2. Database connection in production")
            print("3. Missing dependencies in production")
            print("4. Production logs for specific error")
            
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_common_500_causes():
    """Check common causes of 500 errors"""
    print("\n🔍 Checking Common 500 Error Causes:")
    print("=" * 50)
    
    # Check 1: Missing environment variables
    print("\n1️⃣ Environment Variables:")
    env_vars = ['DATABASE_URL', 'FLASK_ENV', 'SECRET_KEY']
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var}: Set")
        else:
            print(f"❌ {var}: Missing")
    
    # Check 2: Database connection
    print("\n2️⃣ Database Connection:")
    try:
        from app import create_app, db
        app = create_app()
        with app.app_context():
            from sqlalchemy import text
            db.session.execute(text("SELECT 1"))
            print("✅ Database connection: Working")
    except Exception as e:
        print(f"❌ Database connection: Failed - {str(e)}")
    
    # Check 3: Required modules
    print("\n3️⃣ Required Modules:")
    required_modules = ['flask', 'flask_login', 'sqlalchemy', 'werkzeug']
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}: Available")
        except ImportError:
            print(f"❌ {module}: Missing")

if __name__ == "__main__":
    print("🚀 Authentication Debug Tool")
    print("=" * 50)
    
    # Check common causes first
    check_common_500_causes()
    
    # Test login endpoint
    success = test_login_endpoint()
    
    if success:
        print("\n✅ Local tests passed - issue likely in production environment")
        print("\n🔧 To debug production:")
        print("1. Check Render deployment logs")
        print("2. Verify environment variables on Render")
        print("3. Check if database is accessible from production")
        print("4. Look for import errors in production logs")
    else:
        print("\n❌ Local tests failed - fix local issues first")
    
    sys.exit(0 if success else 1)
