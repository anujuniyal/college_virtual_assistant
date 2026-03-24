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
            # Test database connection first
            print("🔍 Testing database connection...")
            try:
                db.session.execute("SELECT 1")
                print("✅ Database connection successful")
            except Exception as db_error:
                print(f"❌ Database connection failed: {str(db_error)}")
                print(f"🔧 Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
                raise db_error
            
            # Check if database is already populated
            print("📋 Checking database state...")
            try:
                # Check if Faculty table exists and has data
                faculty_count = db.session.query(Faculty).count()
                print(f"📊 Faculty table found with {faculty_count} records")
                
                if faculty_count > 0:
                    print("✅ Database already populated - skipping table creation")
                    print("🔧 Only creating missing tables if any...")
                    
                    # Create only missing tables (safe operation)
                    from sqlalchemy import inspect
                    inspector = inspect(db.engine)
                    existing_tables = inspector.get_table_names()
                    
                    # Get all expected tables from models
                    all_models = [Faculty]  # Add your other models here
                    expected_tables = [model.__tablename__ for model in all_models]
                    
                    missing_tables = [table for table in expected_tables if table not in existing_tables]
                    
                    if missing_tables:
                        print(f"� Creating missing tables: {missing_tables}")
                        db.create_all()  # This only creates missing tables
                    else:
                        print("✅ All tables already exist")
                else:
                    print("�📋 Database empty - creating all tables...")
                    db.create_all()
                    print("✅ Database tables created")
                    
            except Exception as check_error:
                print(f"⚠️  Error checking database state: {str(check_error)}")
                print("📋 Proceeding with table creation...")
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
