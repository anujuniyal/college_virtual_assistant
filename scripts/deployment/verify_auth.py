#!/usr/bin/env python3
"""
Deployment verification script for authentication
Checks database connection, table structure, and authentication functionality
"""

import os
import sys
from sqlalchemy import inspect, text

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def verify_authentication():
    """Verify authentication setup"""
    try:
        from app import create_app, db
        from app.models import Faculty
        from app.services.user_service import UserService
        
        print("🔍 Verifying Authentication Setup...")
        
        # Create app context
        app = create_app()
        with app.app_context():
            print("✅ App context created")
            
            # Test database connection
            try:
                db.session.execute(text("SELECT 1"))
                print("✅ Database connection successful")
            except Exception as e:
                print(f"❌ Database connection failed: {str(e)}")
                return False
            
            # Check table structure
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"📋 Available tables: {tables}")
            
            # Verify Faculty table exists
            if 'faculty' in tables:
                print("✅ Faculty table exists")
            else:
                print("❌ Faculty table missing")
                return False
            
            # Check if Admin table exists (should not exist in deployment)
            if 'admins' in tables:
                print("⚠️  Admin table exists (may cause conflicts)")
            else:
                print("✅ Admin table does not exist (correct for deployment)")
            
            # Check faculty table structure
            faculty_columns = inspector.get_columns('faculty')
            required_columns = ['id', 'name', 'email', 'role', 'password_hash']
            
            for col in required_columns:
                if any(c['name'] == col for c in faculty_columns):
                    print(f"✅ Faculty table has {col} column")
                else:
                    print(f"❌ Faculty table missing {col} column")
                    return False
            
            # Check if default admin exists in Faculty table
            admin_user = Faculty.query.filter_by(email='admin@edubot.com').first()
            if admin_user:
                print("✅ Default admin user exists in Faculty table")
                print(f"   - Email: {admin_user.email}")
                print(f"   - Role: {admin_user.role}")
                print(f"   - Name: {admin_user.name}")
            else:
                print("⚠️  Default admin user not found in Faculty table")
                print("   Creating default admin user...")
                
                # Create default admin
                admin = Faculty(
                    name='Default Admin',
                    email='admin@edubot.com',
                    department='Administration',
                    role='admin',
                    phone='N/A'
                )
                admin.set_password('admin123')
                
                db.session.add(admin)
                db.session.commit()
                
                print("✅ Default admin user created in Faculty table")
            
            # Test authentication
            print("\n🔐 Testing authentication...")
            auth_result = UserService.authenticate_user('admin@edubot.com', 'admin123')
            
            if auth_result['success']:
                print("✅ Authentication successful")
                print(f"   - User: {auth_result['user'].name}")
                print(f"   - Role: {auth_result['user'].role}")
            else:
                print(f"❌ Authentication failed: {auth_result['message']}")
                return False
            
            # Test wrong password
            wrong_auth = UserService.authenticate_user('admin@edubot.com', 'wrongpassword')
            if not wrong_auth['success']:
                print("✅ Wrong password correctly rejected")
            else:
                print("❌ Wrong password was accepted")
                return False
            
            # Test non-existent user
            nonexistent_auth = UserService.authenticate_user('nonexistent@test.com', 'password')
            if not nonexistent_auth['success']:
                print("✅ Non-existent user correctly rejected")
            else:
                print("❌ Non-existent user was accepted")
                return False
            
            print("\n🎉 All authentication checks passed!")
            return True
            
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify_authentication()
    sys.exit(0 if success else 1)
