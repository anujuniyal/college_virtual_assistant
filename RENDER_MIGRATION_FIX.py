#!/usr/bin/env python3
"""
Quick Render Migration Fix
Apply database migration directly on Render
"""
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.extensions import db
from app import create_app
from sqlalchemy import text

def quick_migration():
    """Quick fix for Render database field length issues"""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("=== RENDER DATABASE MIGRATION ===")
            
            # Fix all phone number fields
            migrations = [
                ("students", "phone"),
                ("student_registrations", "phone"), 
                ("visitor_queries", "phone_number")
            ]
            
            for table, column in migrations:
                try:
                    alter_sql = f"ALTER TABLE {table} ALTER COLUMN {column} TYPE VARCHAR(20);"
                    db.session.execute(text(alter_sql))
                    print(f"Updated {table}.{column} to VARCHAR(20)")
                except Exception as e:
                    if "already exists" in str(e).lower() or "does not exist" in str(e).lower():
                        print(f"Skipped {table}.{column}: {str(e)}")
                    else:
                        print(f"Error updating {table}.{column}: {str(e)}")
            
            # Commit changes
            db.session.commit()
            print("Migration completed successfully!")
            
            # Verify changes
            print("\n=== VERIFICATION ===")
            for table, column in migrations:
                try:
                    verify_sql = f"""
                    SELECT column_name, character_maximum_length 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' AND column_name = '{column}';
                    """
                    result = db.session.execute(text(verify_sql))
                    for row in result:
                        print(f"{table}.{column}: {row[1]} characters")
                except Exception as e:
                    print(f"Could not verify {table}.{column}: {str(e)}")
            
            return True
            
        except Exception as e:
            print(f"Migration failed: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    print("Starting Render database migration...")
    success = quick_migration()
    
    if success:
        print("Migration completed! Bot should work now.")
    else:
        print("Migration failed. Check logs for details.")
    
    sys.exit(0 if success else 1)
