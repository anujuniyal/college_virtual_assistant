#!/usr/bin/env python3
"""
Migration script to update phone field length from 15 to 20 characters
"""
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.extensions import db
from app import create_app
from sqlalchemy import text

def migrate_phone_field_length():
    """Update phone field length in students table from varchar(15) to varchar(20)"""
    
    app = create_app()
    
    with app.app_context():
        try:
            # Update the phone column in students table
            alter_sql = """
            ALTER TABLE students 
            ALTER COLUMN phone TYPE VARCHAR(20);
            """
            
            # Also update phone column in student_registrations table if it exists
            alter_reg_sql = """
            ALTER TABLE student_registrations 
            ALTER COLUMN phone TYPE VARCHAR(20);
            """
            
            # Update phone column in visitor_queries table
            alter_visitor_sql = """
            ALTER TABLE visitor_queries 
            ALTER COLUMN phone_number TYPE VARCHAR(20);
            """
            
            print("🔄 Updating phone field length from 15 to 20 characters...")
            
            # Execute the migration for students table
            db.session.execute(text(alter_sql))
            print(" Updated students.phone field to VARCHAR(20)")
            
            # Check if student_registrations table exists and update it
            try:
                db.session.execute(text(alter_reg_sql))
                print("Updated student_registrations.phone field to VARCHAR(20)")
            except Exception as e:
                if "does not exist" in str(e).lower():
                    print("student_registrations table does not exist, skipping...")
                else:
                    print(f"Error updating student_registrations: {e}")
            
            # Check if visitor_queries table exists and update it
            try:
                db.session.execute(text(alter_visitor_sql))
                print("Updated visitor_queries.phone_number field to VARCHAR(20)")
            except Exception as e:
                if "does not exist" in str(e).lower():
                    print("visitor_queries table does not exist, skipping...")
                else:
                    print(f"Error updating visitor_queries: {e}")
            
            # Commit the changes
            db.session.commit()
            print(" Migration completed successfully!")
            
            # Verify the change
            verify_sql = """
            SELECT column_name, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = 'students' AND column_name = 'phone';
            """
            
            result = db.session.execute(text(verify_sql))
            for row in result:
                print(f"✅ Verified: students.phone field length is now {row[1]} characters")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            db.session.rollback()
            return False
        
        return True

if __name__ == '__main__':
    print("🚀 Starting phone field length migration...")
    success = migrate_phone_field_length()
    
    if success:
        print("🎉 Migration completed successfully!")
    else:
        print("💥 Migration failed!")
        sys.exit(1)
