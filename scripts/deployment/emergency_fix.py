#!/usr/bin/env python3
"""
Emergency fix for deployment authentication
Forces database connection and creates admin user
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def emergency_database_fix():
    """Emergency fix for database connection"""
    print("🚨 EMERGENCY DEPLOYMENT FIX")
    print("=" * 50)
    
    try:
        # Force production environment
        os.environ['FLASK_ENV'] = 'production'
        
        # Force database URL from Render environment
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not found in environment")
            return False
        
        print(f"📡 DATABASE_URL found: {database_url.split('@')[1] if '@' in database_url else 'Unknown'}")
        
        # Override any existing database configuration
        os.environ['DATABASE_URL'] = database_url
        
        from app import create_app, db
        from app.models import Faculty
        from werkzeug.security import generate_password_hash
        
        app = create_app()
        
        with app.app_context():
            # Test database connection
            try:
                from sqlalchemy import text
                db.session.execute(text("SELECT 1"))
                print("✅ Database connection successful")
            except Exception as e:
                print(f"❌ Database connection failed: {e}")
                return False
            
            # Check if admin user exists
            admin_user = Faculty.query.filter_by(email='admin@edubot.com').first()
            if admin_user:
                print("✅ Admin user already exists")
                print(f"   Email: {admin_user.email}")
                print(f"   Role: {admin_user.role}")
                print(f"   ID: {admin_user.id}")
                
                # Test password
                if admin_user.check_password('admin123'):
                    print("✅ Admin password is correct")
                else:
                    print("❌ Admin password is incorrect - resetting...")
                    admin_user.set_password('admin123')
                    db.session.commit()
                    print("✅ Admin password reset to admin123")
                
                return True
            else:
                print("❌ Admin user not found - creating...")
                
                # Create admin user
                admin_user = Faculty(
                    name='Default Admin',
                    email='admin@edubot.com',
                    department='Administration',
                    role='admin',
                    phone='N/A'
                )
                admin_user.set_password('admin123')
                
                db.session.add(admin_user)
                db.session.commit()
                
                print("✅ Admin user created successfully")
                print(f"   Email: admin@edubot.com")
                print(f"   Password: admin123")
                print(f"   Role: admin")
                print(f"   ID: {admin_user.id}")
                
                return True
                
    except Exception as e:
        print(f"❌ Emergency fix failed: {str(e)}")
        return False

def main():
    """Main emergency fix function"""
    success = emergency_database_fix()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ EMERGENCY FIX COMPLETED!")
        print("🎯 Authentication should now work")
        print("📋 Login: admin@edubot.com / admin123")
    else:
        print("❌ EMERGENCY FIX FAILED!")
        print("🔧 Manual intervention required")
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
