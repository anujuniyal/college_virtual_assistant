#!/usr/bin/env python3
"""
Test Supabase database connection
"""

import os
import sys

# Set environment variables
os.environ['DATABASE_URL'] = 'postgresql://postgres:anujajuniyal007@db.sqzpzxcmhgkbvjfuxgsk.supabase.co:5432/postgres'
os.environ['FLASK_ENV'] = 'production'

def test_connection():
    """Test connection to Supabase database"""
    try:
        from app import create_app, db
        from app.models import Faculty
        
        print("🔍 Testing Supabase connection...")
        
        app = create_app()
        
        with app.app_context():
            # Test basic connection
            result = db.session.execute('SELECT version()')
            print(f"✅ Connected to: {result.fetchone()[0]}")
            
            # Check if tables exist
            print("\n📋 Checking existing tables...")
            tables = db.session.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """).fetchall()
            
            if tables:
                print(f"✅ Found {len(tables)} tables:")
                for table in tables:
                    print(f"   - {table[0]}")
            else:
                print("❌ No tables found")
            
            # Check Faculty table data
            print("\n👤 Checking Faculty table...")
            try:
                faculty_count = db.session.query(Faculty).count()
                print(f"✅ Faculty table has {faculty_count} records")
                
                if faculty_count > 0:
                    # Show first few records
                    sample_faculty = db.session.query(Faculty).limit(3).all()
                    print("Sample records:")
                    for faculty in sample_faculty:
                        print(f"   - {faculty.name} ({faculty.email}) - {faculty.role}")
                
                # Check for admin user
                admin_user = Faculty.query.filter_by(email='admin@edubot.com').first()
                if admin_user:
                    print("✅ Default admin user exists")
                else:
                    print("⚠️  Default admin user not found")
                
            except Exception as e:
                print(f"❌ Error checking Faculty table: {str(e)}")
            
            print("\n🎉 Supabase connection test successful!")
            return True
            
    except Exception as e:
        print(f"❌ Connection test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
