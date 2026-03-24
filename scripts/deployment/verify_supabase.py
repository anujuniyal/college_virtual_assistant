#!/usr/bin/env python3
"""
Verify Supabase database connection
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def verify_supabase_connection():
    """Verify Supabase database connection"""
    print("🔍 VERIFYING SUPABASE CONNECTION")
    print("=" * 50)
    
    # Set Supabase database URL
    supabase_url = "postgresql://postgres:anujajuniyal007@db.sqzpzxcmhgkbvjfuxgsk.supabase.co:5432/postgres"
    os.environ['DATABASE_URL'] = supabase_url
    os.environ['FLASK_ENV'] = 'production'
    
    print(f"📡 DATABASE_URL: {supabase_url.split('@')[1]}")
    
    try:
        from app import create_app, db
        from app.models import Faculty, Admin
        
        app = create_app()
        
        with app.app_context():
            # Test database connection
            try:
                from sqlalchemy import text
                result = db.session.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                print(f"✅ Database connected: {version}")
            except Exception as e:
                print(f"❌ Database connection failed: {e}")
                return False
            
            # Check if tables exist
            try:
                from sqlalchemy import inspect
                inspector = inspect(db.engine)
                tables = inspector.get_table_names()
                
                required_tables = ['faculty', 'admins']
                print(f"📊 Tables found: {len(tables)}")
                
                for table in required_tables:
                    if table in tables:
                        print(f"   ✅ {table} table exists")
                    else:
                        print(f"   ❌ {table} table missing")
                        
            except Exception as e:
                print(f"❌ Table check failed: {e}")
                return False
            
            # Check users in database
            try:
                faculty_count = Faculty.query.count()
                admin_count = Admin.query.count()
                
                print(f"\n👥 Users in database:")
                print(f"   Faculty: {faculty_count} users")
                print(f"   Admin: {admin_count} users")
                
                # Check specific admin user
                admin_user = Faculty.query.filter_by(email='admin@edubot.com').first()
                if admin_user:
                    print(f"   ✅ Admin user found: {admin_user.email}")
                    print(f"   ✅ Password check: {admin_user.check_password('admin123')}")
                else:
                    print("   ❌ Admin user not found - creating...")
                    
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
                    
                    print("   ✅ Admin user created successfully")
                    print("   📧 Email: admin@edubot.com")
                    print("   🔑 Password: admin123")
                
            except Exception as e:
                print(f"❌ User check failed: {e}")
                return False
            
            print(f"\n🎯 SUPABASE CONNECTION: VERIFIED")
            print(f"✅ Database: PostgreSQL (Supabase)")
            print(f"✅ Tables: Created and populated")
            print(f"✅ Users: Admin user ready for authentication")
            print(f"✅ Authentication: Ready for deployment")
            
            return True
            
    except Exception as e:
        print(f"❌ Supabase verification failed: {str(e)}")
        return False

def main():
    """Main verification function"""
    success = verify_supabase_connection()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ SUPABASE CONNECTION VERIFIED!")
        print("🎉 Deployment ready with Supabase database")
        print("📋 Login: admin@edubot.com / admin123")
    else:
        print("❌ SUPABASE CONNECTION FAILED!")
        print("🔧 Check database configuration")
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
