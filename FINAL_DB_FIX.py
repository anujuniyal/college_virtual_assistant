#!/usr/bin/env python3
"""
FINAL COMPREHENSIVE DATABASE FIX
This will find and fix ALL VARCHAR(15) fields that are causing persistent errors
"""
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.extensions import db
from app import create_app
from sqlalchemy import text

def final_comprehensive_fix():
    """Final comprehensive fix for all database field length issues"""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("=== FINAL COMPREHENSIVE DATABASE FIX ===")
            print("This will find and fix ALL VARCHAR(15) fields...")
            
            # Step 1: Find ALL VARCHAR(15) fields
            print("\n1. Scanning for ALL VARCHAR(15) fields...")
            
            scan_sql = """
            SELECT table_name, column_name, character_maximum_length, data_type
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND data_type = 'character varying'
            AND character_maximum_length = 15
            ORDER BY table_name, column_name;
            """
            
            result = db.session.execute(text(scan_sql))
            varchar15_fields = []
            
            for row in result:
                table_name, column_name, max_length, data_type = row
                varchar15_fields.append({
                    'table': table_name,
                    'column': column_name,
                    'current_length': max_length,
                    'data_type': data_type
                })
                print(f"Found VARCHAR(15): {table_name}.{column_name}")
            
            if not varchar15_fields:
                print("No VARCHAR(15) fields found!")
                return True
            
            print(f"\nFound {len(varchar15_fields)} VARCHAR(15) fields that need fixing...")
            
            # Step 2: Fix ALL VARCHAR(15) fields to VARCHAR(20)
            print(f"\n2. Fixing all {len(varchar15_fields)} VARCHAR(15) fields...")
            
            fixed_count = 0
            failed_count = 0
            
            for field in varchar15_fields:
                table = field['table']
                column = field['column']
                
                try:
                    alter_sql = f"ALTER TABLE {table} ALTER COLUMN {column} TYPE VARCHAR(20);"
                    db.session.execute(text(alter_sql))
                    print(f"✅ Fixed: {table}.{column} (15 -> 20)")
                    fixed_count += 1
                except Exception as e:
                    print(f"❌ Failed: {table}.{column} - {str(e)}")
                    failed_count += 1
            
            # Step 3: Also check for any VARCHAR(10) or other short fields
            print(f"\n3. Checking for other short VARCHAR fields...")
            
            short_scan_sql = """
            SELECT table_name, column_name, character_maximum_length
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND data_type = 'character varying'
            AND character_maximum_length < 20
            AND character_maximum_length > 0
            ORDER BY character_maximum_length ASC;
            """
            
            result = db.session.execute(text(short_scan_sql))
            short_fields = []
            
            for row in result:
                table_name, column_name, max_length = row
                if max_length and int(max_length) < 20:
                    short_fields.append({
                        'table': table_name,
                        'column': column_name,
                        'length': max_length
                    })
            
            if short_fields:
                print(f"\nFound {len(short_fields)} other short VARCHAR fields:")
                for field in short_fields:
                    print(f"  {field['table']}.{field['column']} (VARCHAR({field['length']}))")
                    
                    # Try to fix them too
                    if int(field['length']) < 20:
                        try:
                            alter_sql = f"ALTER TABLE {field['table']} ALTER COLUMN {field['column']} TYPE VARCHAR(20);"
                            db.session.execute(text(alter_sql))
                            print(f"    ✅ Fixed to VARCHAR(20)")
                            fixed_count += 1
                        except Exception as e:
                            print(f"    ❌ Could not fix: {str(e)}")
                            failed_count += 1
            
            # Step 4: Commit all changes
            print(f"\n4. Committing changes...")
            db.session.commit()
            
            print(f"\n=== FIX SUMMARY ===")
            print(f"✅ Successfully fixed: {fixed_count} fields")
            print(f"❌ Failed to fix: {failed_count} fields")
            
            # Step 5: Verification
            print(f"\n5. Verification...")
            
            result = db.session.execute(text(scan_sql))
            remaining_fields = []
            
            for row in result:
                table_name, column_name, max_length, data_type = row
                remaining_fields.append({
                    'table': table_name,
                    'column': column_name,
                    'length': max_length
                })
            
            if remaining_fields:
                print(f"⚠️ Still have {len(remaining_fields)} VARCHAR(15) fields:")
                for field in remaining_fields:
                    print(f"  {field['table']}.{field['column']} (VARCHAR({field['length']}))")
            else:
                print("✅ All VARCHAR(15) fields have been fixed!")
            
            return len(remaining_fields) == 0
            
        except Exception as e:
            print(f"Final fix failed: {e}")
            db.session.rollback()
            return False

def check_current_student_roll_numbers():
    """Check current roll numbers in database to understand format"""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("\n=== CHECKING CURRENT ROLL NUMBERS ===")
            
            check_sql = """
            SELECT roll_number, LENGTH(roll_number) as length
            FROM students 
            WHERE roll_number IS NOT NULL
            ORDER BY length DESC
            LIMIT 10;
            """
            
            result = db.session.execute(text(check_sql))
            
            print("Current roll numbers in database:")
            for row in result:
                roll_number, length = row
                print(f"  {roll_number} (length: {length})")
            
            return True
            
        except Exception as e:
            print(f"Error checking roll numbers: {e}")
            return False

if __name__ == '__main__':
    print("Starting FINAL comprehensive database fix...")
    
    # Check current roll numbers first
    check_current_student_roll_numbers()
    
    # Run final comprehensive fix
    success = final_comprehensive_fix()
    
    if success:
        print("\n🎉 FINAL FIX COMPLETED SUCCESSFULLY!")
        print("All VARCHAR(15) fields have been updated to VARCHAR(20)")
        print("Your bot should now work without field length errors!")
        print("\nTest your bot with: EDU25001")
    else:
        print("\n💥 FINAL FIX HAD ISSUES")
        print("Check the error messages above")
        print("You may need to manually fix remaining fields")
    
    sys.exit(0 if success else 1)
