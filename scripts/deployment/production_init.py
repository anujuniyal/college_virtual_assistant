#!/usr/bin/env python3
"""
Production startup script for Render
Handles database initialization on first start
"""

import os
import sys

# Set production environment
os.environ['FLASK_ENV'] = 'production'

def initialize_production():
    """Initialize database and create default admin on first start"""
    try:
        from app import create_app, db
        from app.models import Faculty
        from app.services.user_service import UserService
        
        print("🚀 Starting production initialization...")
        
        app = create_app()
        
        with app.app_context():
            # Create all tables
            print("📋 Creating database tables...")
            db.create_all()
            print("✅ Database tables created")
            
            # Check if default admin exists
            admin_email = os.environ.get('DEFAULT_ADMIN_EMAIL', 'admin@edubot.com')
            admin_password = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'admin123')
            
            admin_user = Faculty.query.filter_by(email=admin_email).first()
            if not admin_user:
                print("👤 Creating default admin user...")
                admin = Faculty(
                    name='Default Admin',
                    email=admin_email,
                    department='Administration',
                    role='admin',
                    phone='N/A'
                )
                admin.set_password(admin_password)
                
                db.session.add(admin)
                db.session.commit()
                print(f"✅ Default admin created: {admin_email}")
            else:
                print(f"✅ Default admin already exists: {admin_email}")
            
            # Test authentication
            result = UserService.authenticate_user(admin_email, admin_password)
            if result['success']:
                print("✅ Authentication test passed")
            else:
                print(f"❌ Authentication test failed: {result['message']}")
                return False
            
            print("🎉 Production initialization complete!")
            return True
            
    except Exception as e:
        print(f"❌ Production initialization failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = initialize_production()
    sys.exit(0 if success else 1)
