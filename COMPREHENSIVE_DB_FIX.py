#!/usr/bin/env python3
"""
Comprehensive Database Fix for All Phone Field Length Issues
This script identifies and fixes ALL tables with phone field length problems
"""
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.extensions import db
from app import create_app
from sqlalchemy import text

def find_and_fix_all_phone_fields():
    """Find and fix all phone-related fields with length issues"""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("=== COMPREHENSIVE DATABASE FIELD FIX ===")
            
            # Step 1: Find all phone-related fields
            print("\n1. Scanning for phone-related fields...")
            
            scan_sql = """
            SELECT table_name, column_name, character_maximum_length, data_type
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND (column_name LIKE '%phone%' OR column_name LIKE '%Phone%')
            AND data_type = 'character varying'
            ORDER BY table_name, column_name;
            """
            
            result = db.session.execute(text(scan_sql))
            phone_fields = []
            
            for row in result:
                table_name, column_name, max_length, data_type = row
                phone_fields.append({
                    'table': table_name,
                    'column': column_name,
                    'current_length': max_length,
                    'data_type': data_type
                })
                print(f"Found: {table_name}.{column_name} (VARCHAR({max_length}))")
            
            if not phone_fields:
                print("No phone fields found with length issues")
                return True
            
            # Step 2: Fix all phone fields that are less than 20 characters
            print(f"\n2. Fixing {len(phone_fields)} phone fields...")
            
            fixed_count = 0
            for field in phone_fields:
                table = field['table']
                column = field['column']
                current_length = field['current_length']
                
                if current_length and int(current_length) < 20:
                    try:
                        alter_sql = f"ALTER TABLE {table} ALTER COLUMN {column} TYPE VARCHAR(20);"
                        db.session.execute(text(alter_sql))
                        print(f"Fixed: {table}.{column} {current_length} -> 20")
                        fixed_count += 1
                    except Exception as e:
                        print(f"Error fixing {table}.{column}: {str(e)}")
                else:
                    print(f"Skipped: {table}.{column} (already {current_length} characters)")
            
            # Step 3: Look for any other fields that might be causing issues
            print(f"\n3. Checking for other potential issues...")
            
            # Check for any VARCHAR fields that might be too short for common data
            other_scan_sql = """
            SELECT table_name, column_name, character_maximum_length
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND data_type = 'character varying'
            AND character_maximum_length < 20
            AND character_maximum_length IS NOT NULL
            ORDER BY character_maximum_length ASC;
            """
            
            result = db.session.execute(text(other_scan_sql))
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
                for field in short_fields[:10]:  # Show first 10
                    print(f"  {field['table']}.{field['column']} (VARCHAR({field['length']}))")
            
            # Step 4: Commit all changes
            print(f"\n4. Committing changes...")
            db.session.commit()
            print(f"Successfully fixed {fixed_count} phone fields!")
            
            # Step 5: Verification
            print(f"\n5. Verification...")
            result = db.session.execute(text(scan_sql))
            
            for row in result:
                table_name, column_name, max_length, data_type = row
                status = "OK" if (max_length and int(max_length) >= 20) else "STILL SHORT"
                print(f"{table_name}.{column_name}: VARCHAR({max_length}) - {status}")
            
            return True
            
        except Exception as e:
            print(f"Comprehensive fix failed: {e}")
            db.session.rollback()
            return False

def check_specific_error():
    """Check for the specific error mentioned in the logs"""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("\n=== CHECKING SPECIFIC ERROR ===")
            
            # Look for any INSERT that might be failing
            error_check_sql = """
            SELECT table_name, column_name, character_maximum_length
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND data_type = 'character varying'
            AND character_maximum_length = 15
            ORDER BY table_name, column_name;
            """
            
            result = db.session.execute(text(error_check_sql))
            problem_fields = []
            
            for row in result:
                table_name, column_name, max_length = row
                problem_fields.append({
                    'table': table_name,
                    'column': column_name,
                    'length': max_length
                })
                print(f"Potential issue: {table_name}.{column_name} (VARCHAR({max_length}))")
            
            if problem_fields:
                print(f"\nFound {len(problem_fields)} fields with VARCHAR(15) that might be causing issues:")
                for field in problem_fields:
                    # Try to fix them
                    try:
                        alter_sql = f"ALTER TABLE {field['table']} ALTER COLUMN {field['column']} TYPE VARCHAR(20);"
                        db.session.execute(text(alter_sql))
                        print(f"Fixed: {field['table']}.{field['column']}")
                    except Exception as e:
                        print(f"Could not fix {field['table']}.{field['column']}: {str(e)}")
                
                db.session.commit()
                print("Applied fixes to VARCHAR(15) fields")
            
            return True
            
        except Exception as e:
            print(f"Error check failed: {e}")
            return False

if __name__ == '__main__':
    print("Starting comprehensive database fix...")
    
    # Run comprehensive fix
    success1 = find_and_fix_all_phone_fields()
    
    # Run specific error check
    success2 = check_specific_error()
    
    if success1 and success2:
        print("\n=== COMPREHENSIVE FIX COMPLETED ===")
        print("All database field issues should now be resolved!")
        print("Test your bot with: register EDU2025001")
    else:
        print("\n=== FIX HAD ISSUES ===")
        print("Check the error messages above")
    
    sys.exit(0 if (success1 and success2) else 1)
