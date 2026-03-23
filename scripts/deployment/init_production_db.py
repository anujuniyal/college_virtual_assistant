#!/usr/bin/env python3
"""
Production Database Initialization Script
This script initializes the production database with required tables and default admin user.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set production environment
os.environ['FLASK_ENV'] = 'production'

from app import create_app, db
from app.models import Admin, Faculty
from app.services.user_service import UserService

def init_production_database():
    """Initialize production database with tables and default admin"""
    app = create_app()
    
    with app.app_context():
        try:
            print("Creating database tables...")
            db.create_all()
            print("✓ Database tables created successfully")
            
            # Initialize default admin in Faculty table (since auth uses Faculty table)
            print("Creating default admin user...")
            admin = UserService.initialize_default_admin()
            
            if admin:
                print(f"✓ Default admin created: {admin.email} with password 'admin123'")
            else:
                print("⚠ Default admin may already exist or failed to create")
            
            # Check if admin exists in Admin table too (for compatibility)
            existing_admin = Admin.query.filter_by(email='admin@edubot.com').first()
            if not existing_admin:
                # Check if username already exists
                existing_username = Admin.query.filter_by(username='admin').first()
                if existing_username:
                    # Use different username if admin already taken
                    admin_user = Admin(
                        username='admin_user',
                        email='admin@edubot.com',
                        role='admin'
                    )
                else:
                    admin_user = Admin(
                        username='admin',
                        email='admin@edubot.com',
                        role='admin'
                    )
                admin_user.set_password('admin123')
                db.session.add(admin_user)
                db.session.commit()
                print("✓ Admin user created in Admin table")
            else:
                print("✓ Admin user already exists in Admin table")
            
            print("\n🎉 Production database initialized successfully!")
            print("\nLogin credentials:")
            print("Email: admin@edubot.com")
            print("Password: admin123")
            print("\n⚠️  Please change the default password after first login!")
            
        except Exception as e:
            print(f"❌ Error initializing database: {str(e)}")
            db.session.rollback()
            return False
    
    return True

if __name__ == '__main__':
    success = init_production_database()
    sys.exit(0 if success else 1)
