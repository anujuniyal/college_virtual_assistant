#!/usr/bin/env python3
"""
Deployment Verification Script
Verifies database connection and authentication in deployment
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set production environment
os.environ['FLASK_ENV'] = 'production'

def verify_database_connection():
    """Verify database connection and table structure"""
    try:
        print("🔍 Verifying database connection...")
        
        from app import create_app, db
        from app.models import Admin, Faculty
        
        app = create_app()
        
        with app.app_context():
            # Test database connection
            db.session.execute("SELECT 1")
            print("✅ Database connection successful")
            
            # Check if tables exist
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            required_tables = ['admins', 'faculty']
            for table in required_tables:
                if table in tables:
                    print(f"✅ Table '{table}' exists")
                else:
                    print(f"❌ Table '{table}' missing")
                    return False
            
            # Check admin users
            admin_count = Admin.query.count()
            faculty_count = Faculty.query.count()
            
            print(f"📊 Admin users: {admin_count}")
            print(f"📊 Faculty users: {faculty_count}")
            
            if admin_count == 0 and faculty_count == 0:
                print("⚠️  No users found in database")
                return False
            
            return True
            
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False

def verify_authentication():
    """Test authentication with database users"""
    try:
        print("\n🔐 Verifying authentication...")
        
        from app import create_app
        from app.services.user_service import UserService
        
        app = create_app()
        
        with app.app_context():
            # Test with default admin credentials
            result = UserService.authenticate_user('admin@edubot.com', 'admin123')
            
            if result['success']:
                print("✅ Authentication successful with database")
                print(f"   User: {result['user']}")
                return True
            else:
                print(f"❌ Authentication failed: {result['message']}")
                return False
                
    except Exception as e:
        print(f"❌ Authentication verification failed: {str(e)}")
        return False

def main():
    """Main verification function"""
    print("🚀 Deployment Verification")
    print("=" * 50)
    
    # Set environment variables for deployment
    os.environ['FLASK_ENV'] = 'production'
    
    all_passed = True
    
    # Verify database connection
    if not verify_database_connection():
        all_passed = False
    
    # Verify authentication
    if not verify_authentication():
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All verification checks passed!")
        print("🎉 Deployment is ready for authentication!")
    else:
        print("❌ Some verification checks failed!")
        print("🔧 Please check the errors above and fix deployment issues")
    
    return all_passed

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
