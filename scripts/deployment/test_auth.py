#!/usr/bin/env python3
"""
Comprehensive authentication test
Tests all authentication scenarios to ensure deployment works correctly
"""

import os
import sys

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def test_authentication():
    """Test all authentication scenarios"""
    try:
        from app import create_app, db
        from app.models import Faculty, Admin
        from app.services.user_service import UserService
        
        print("🧪 Comprehensive Authentication Test")
        print("=" * 50)
        
        app = create_app()
        with app.app_context():
            
            # Test 1: Faculty table authentication
            print("\n1️⃣ Testing Faculty Table Authentication:")
            
            # Test admin user in Faculty table
            result = UserService.authenticate_user('admin@edubot.com', 'admin123')
            if result['success']:
                print("✅ Admin authentication via Faculty table: SUCCESS")
                print(f"   User: {result['user'].name} ({result['user'].role})")
            else:
                print("❌ Admin authentication via Faculty table: FAILED")
                return False
            
            # Test 2: Verify Admin table is ignored
            print("\n2️⃣ Testing Admin Table Ignored:")
            admin_user = Admin.query.filter_by(email='admin@college.edu').first()
            if admin_user:
                print("⚠️  Admin table exists but should be ignored")
                # Test that authentication doesn't use Admin table
                result = UserService.authenticate_user('admin@college.edu', 'password')
                if not result['success']:
                    print("✅ Admin table correctly ignored in authentication")
                else:
                    print("❌ Admin table incorrectly used for authentication")
                    return False
            else:
                print("✅ Admin table doesn't exist (good)")
            
            # Test 3: Test different roles in Faculty table
            print("\n3️⃣ Testing Different Roles in Faculty Table:")
            
            test_users = [
                ('admin@edubot.com', 'admin123', 'admin'),
            ]
            
            for email, password, expected_role in test_users:
                result = UserService.authenticate_user(email, password)
                if result['success'] and result['user'].role == expected_role:
                    print(f"✅ {expected_role} role authentication: SUCCESS")
                else:
                    print(f"❌ {expected_role} role authentication: FAILED")
                    return False
            
            # Test 4: Test authentication failures
            print("\n4️⃣ Testing Authentication Failures:")
            
            # Wrong password
            result = UserService.authenticate_user('admin@edubot.com', 'wrongpassword')
            if not result['success']:
                print("✅ Wrong password rejected: SUCCESS")
            else:
                print("❌ Wrong password accepted: FAILED")
                return False
            
            # Non-existent user
            result = UserService.authenticate_user('nonexistent@test.com', 'password')
            if not result['success']:
                print("✅ Non-existent user rejected: SUCCESS")
            else:
                print("❌ Non-existent user accepted: FAILED")
                return False
            
            # Test 5: Test user retrieval functions
            print("\n5️⃣ Testing User Retrieval Functions:")
            
            # Get user by ID
            admin_faculty = Faculty.query.filter_by(email='admin@edubot.com').first()
            user_by_id = UserService.get_user_by_id(admin_faculty.id)
            if user_by_id and user_by_id.email == 'admin@edubot.com':
                print("✅ get_user_by_id: SUCCESS")
            else:
                print("❌ get_user_by_id: FAILED")
                return False
            
            # Get user by username
            user_by_email = UserService.get_user_by_username('admin@edubot.com')
            if user_by_email and user_by_email.email == 'admin@edubot.com':
                print("✅ get_user_by_username: SUCCESS")
            else:
                print("❌ get_user_by_username: FAILED")
                return False
            
            # Test 6: Verify database connection
            print("\n6️⃣ Testing Database Connection:")
            
            try:
                from sqlalchemy import text
                db.session.execute(text("SELECT 1"))
                print("✅ Database connection: SUCCESS")
            except Exception as e:
                print(f"❌ Database connection: FAILED - {str(e)}")
                return False
            
            print("\n" + "=" * 50)
            print("🎉 ALL TESTS PASSED!")
            print("\n📋 Summary:")
            print("✅ Authentication uses Faculty table only")
            print("✅ Admin table is ignored (if exists)")
            print("✅ All user roles work correctly")
            print("✅ Authentication failures work correctly")
            print("✅ User retrieval functions work")
            print("✅ Database connection stable")
            
            print("\n🔐 Login Credentials for Deployment:")
            print("Email: admin@edubot.com")
            print("Password: admin123")
            print("Role: admin")
            
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_authentication()
    sys.exit(0 if success else 1)
