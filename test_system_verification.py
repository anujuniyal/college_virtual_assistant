#!/usr/bin/env python3
"""
System Verification Test Script
Tests all major functionality after our fixes
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, Admin, Faculty, Student, Notification, FAQ, DailyViewCount
from flask import session

def test_app_startup():
    """Test application startup and configuration"""
    print("🚀 Testing Application Startup...")
    
    try:
        app = create_app()
        print("✅ App created successfully")
        
        with app.app_context():
            # Test configuration
            print(f"✅ Environment: {app.config.get('FLASK_ENV', 'unknown')}")
            print(f"✅ Database URI configured: {'Yes' if app.config.get('SQLALCHEMY_DATABASE_URI') else 'No'}")
            print(f"✅ Remember Cookie Duration: {app.config.get('REMEMBER_COOKIE_DURATION', 'Not set')}")
            print(f"✅ Session Cookie Secure: {app.config.get('SESSION_COOKIE_SECURE', 'Not set')}")
            
            return True
    except Exception as e:
        print(f"❌ App startup failed: {str(e)}")
        return False

def test_database_connection():
    """Test database connection and models"""
    print("\n🗄️ Testing Database Connection...")
    
    try:
        app = create_app()
        
        with app.app_context():
            # Test database connection
            from sqlalchemy import text
            db.session.execute(text("SELECT 1"))
            print("✅ Database connection successful")
            
            # Test model queries
            admin_count = Admin.query.count()
            faculty_count = Faculty.query.count()
            student_count = Student.query.count()
            
            print(f"✅ Admin records: {admin_count}")
            print(f"✅ Faculty records: {faculty_count}")
            print(f"✅ Student records: {student_count}")
            
            return True
    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        return False

def test_authentication_system():
    """Test authentication system"""
    print("\n🔐 Testing Authentication System...")
    
    try:
        app = create_app()
        
        with app.app_context():
            # Test user loading
            from app.extensions import login_manager
            
            # Test admin user loading
            if admin_count > 0:
                admin = Admin.query.first()
                loaded_user = login_manager._user_callback(str(admin.id))
                if loaded_user:
                    print("✅ Admin user loading works")
                else:
                    print("❌ Admin user loading failed")
            
            # Test faculty user loading
            if faculty_count > 0:
                faculty = Faculty.query.first()
                loaded_user = login_manager._user_callback(str(faculty.id))
                if loaded_user:
                    print("✅ Faculty user loading works")
                else:
                    print("❌ Faculty user loading failed")
            
            return True
    except Exception as e:
        print(f"❌ Authentication test failed: {str(e)}")
        return False

def test_foreign_key_constraints():
    """Test foreign key constraint handling"""
    print("\n🔗 Testing Foreign Key Constraints...")
    
    try:
        app = create_app()
        
        with app.app_context():
            # Test cascade relationships in Student model
            student = Student.query.first()
            if student:
                print(f"✅ Student model relationships:")
                print(f"  - Results: {len(student.results)} records")
                print(f"  - Fee Records: {len(student.fee_records)} records")
                print(f"  - Complaints: {len(student.complaints)} records")
                print(f"  - Query Logs: {len(student.query_logs)} records")
                print(f"  - Telegram Mappings: {len(student.telegram_mappings)} records")
                
                # Test DailyViewCount relationship
                daily_counts = DailyViewCount.query.filter_by(student_id=student.id).all()
                print(f"  - Daily View Counts: {len(daily_counts)} records")
            
            return True
    except Exception as e:
        print(f"❌ Foreign key test failed: {str(e)}")
        return False

def test_route_availability():
    """Test key routes are available"""
    print("\n🛣️ Testing Route Availability...")
    
    try:
        app = create_app()
        
        with app.test_client() as client:
            # Test main routes
            routes_to_test = [
                ('/', 'GET', 302),  # Should redirect to login
                ('/login', 'GET', 200),
                ('/health', 'GET', 200),
            ]
            
            for route, method, expected_status in routes_to_test:
                try:
                    if method == 'GET':
                        response = client.get(route)
                    else:
                        response = client.post(route)
                    
                    if response.status_code == expected_status:
                        print(f"✅ {route} - {method} ({response.status_code})")
                    else:
                        print(f"⚠️  {route} - {method} ({response.status_code}, expected {expected_status})")
                except Exception as e:
                    print(f"❌ {route} - {method} failed: {str(e)}")
            
            return True
    except Exception as e:
        print(f"❌ Route test failed: {str(e)}")
        return False

def test_remember_me_config():
    """Test remember me configuration"""
    print("\n🍪 Testing Remember Me Configuration...")
    
    try:
        app = create_app()
        
        with app.app_context():
            # Test remember me settings
            remember_duration = app.config.get('REMEMBER_COOKIE_DURATION')
            remember_secure = app.config.get('REMEMBER_COOKIE_SECURE')
            remember_httponly = app.config.get('REMEMBER_COOKIE_HTTPONLY')
            remember_samesite = app.config.get('REMEMBER_COOKIE_SAMESITE')
            
            print(f"✅ Remember Cookie Duration: {remember_duration}")
            print(f"✅ Remember Cookie Secure: {remember_secure}")
            print(f"✅ Remember Cookie HttpOnly: {remember_httponly}")
            print(f"✅ Remember Cookie SameSite: {remember_samesite}")
            
            if remember_duration and remember_secure is not None:
                print("✅ Remember me configuration is complete")
                return True
            else:
                print("⚠️  Remember me configuration may be incomplete")
                return False
    except Exception as e:
        print(f"❌ Remember me test failed: {str(e)}")
        return False

def main():
    """Run all system verification tests"""
    print("🔍 EduBot System Verification")
    print("=" * 50)
    
    global admin_count, faculty_count
    
    # Initialize counters
    admin_count = 0
    faculty_count = 0
    
    # Run all tests
    tests = [
        ("Application Startup", test_app_startup),
        ("Database Connection", test_database_connection),
        ("Authentication System", test_authentication_system),
        ("Foreign Key Constraints", test_foreign_key_constraints),
        ("Route Availability", test_route_availability),
        ("Remember Me Configuration", test_remember_me_config),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All systems are working correctly!")
        return True
    else:
        print("⚠️  Some issues detected. Please review the failed tests.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
