#!/usr/bin/env python3
"""
Fixed Migration Script: SQLite to Supabase with proper data type conversion
"""

import os
import sys
import sqlite3
import psycopg2
from dotenv import load_dotenv

def convert_value_for_postgres(value, column_name=None):
    """Convert SQLite value to PostgreSQL compatible format"""
    if value is None:
        return None
    
    # Handle boolean conversion
    if column_name in ['is_active', 'telegram_verified', 'verified', 'is_used'] and isinstance(value, int):
        return bool(value)
    
    # Handle empty strings
    if isinstance(value, str) and value == '':
        return None
    
    # Handle string length limits
    if isinstance(value, str):
        if column_name == 'phone' and len(value) > 15:
            return value[:15]  # Truncate phone numbers
        if column_name == 'roll_number' and len(value) > 20:
            return value[:20]
        if column_name == 'email' and len(value) > 120:
            return value[:120]
    
    # Handle bytes
    if isinstance(value, bytes):
        try:
            return value.decode('utf-8')
        except:
            return str(value)
    
    return value

def migrate_data():
    """Migrate data from SQLite to Supabase with proper type conversion"""
    
    # Load production environment
    load_dotenv('.env.production')
    
    # Get database URLs
    sqlite_path = 'instance/edubot_management.db'
    supabase_url = os.environ.get('DATABASE_URL')
    
    if not supabase_url:
        print("❌ DATABASE_URL not found in .env.production")
        return False
    
    if supabase_url.startswith('postgres://'):
        supabase_url = supabase_url.replace('postgres://', 'postgresql://', 1)
    
    print(f"🔗 Connecting to Supabase...")
    print(f"📁 SQLite database: {sqlite_path}")
    
    try:
        # Connect to databases
        sqlite_conn = sqlite3.connect(sqlite_path)
        pg_conn = psycopg2.connect(supabase_url)
        
        sqlite_cursor = sqlite_conn.cursor()
        pg_cursor = pg_conn.cursor()
        
        print("✅ Connected to both databases")
        
        # First, ensure all tables exist in Supabase
        print("🏗️  Ensuring Supabase tables exist...")
        os.system("python scripts/setup_supabase.py setup > /dev/null 2>&1")
        
        # Get all tables from SQLite
        sqlite_cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        tables = [row[0] for row in sqlite_cursor.fetchall()]
        
        print(f"📋 Found {len(tables)} tables to migrate")
        
        total_migrated = 0
        
        # Migrate in dependency order (admins first, then others)
        table_order = ['admins', 'faculty', 'students', 'notifications', 'results', 
                      'fee_records', 'complaints', 'student_registrations', 
                      'telegram_user_mappings', 'otp_verifications', 'predefined_info',
                      'faq_records', 'chatbot_qa', 'chatbot_unknown', 'visitor_queries',
                      'query_logs', 'daily_view_counts', 'sessions', 'notification_deliveries',
                      'faq']
        
        # Sort tables according to dependency order
        ordered_tables = []
        for table in table_order:
            if table in tables:
                ordered_tables.append(table)
        
        # Add any remaining tables
        for table in tables:
            if table not in ordered_tables:
                ordered_tables.append(table)
        
        for table in ordered_tables:
            print(f"\n📊 Migrating {table}...")
            
            try:
                # Get data from SQLite
                sqlite_cursor.execute(f"SELECT * FROM {table}")
                rows = sqlite_cursor.fetchall()
                
                if not rows:
                    print(f"   ✅ No data in {table}")
                    continue
                
                # Get column names
                sqlite_cursor.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in sqlite_cursor.fetchall()]
                
                print(f"   📄 Found {len(rows)} records with {len(columns)} columns")
                
                # Clear existing data in Supabase (be careful with foreign keys)
                try:
                    pg_cursor.execute(f"DELETE FROM {table}")
                except Exception as e:
                    if "foreign key constraint" in str(e).lower():
                        print(f"   ⚠️  Skipping clear due to foreign key constraints")
                    else:
                        raise
                
                # Insert data into Supabase
                placeholders = ', '.join(['%s'] * len(columns))
                columns_str = ', '.join(columns)
                insert_query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
                
                migrated_count = 0
                for row in rows:
                    try:
                        # Convert data for PostgreSQL with proper type handling
                        converted_row = []
                        for i, value in enumerate(row):
                            column_name = columns[i] if i < len(columns) else None
                            converted_row.append(convert_value_for_postgres(value, column_name))
                        
                        pg_cursor.execute(insert_query, converted_row)
                        migrated_count += 1
                        
                    except Exception as e:
                        print(f"   ⚠️  Error inserting row: {str(e)[:100]}...")
                        continue
                
                pg_conn.commit()
                print(f"   ✅ Migrated {migrated_count} records from {table}")
                total_migrated += migrated_count
                
            except Exception as e:
                print(f"   ❌ Error migrating {table}: {str(e)}")
                pg_conn.rollback()
                continue
        
        # Close connections
        sqlite_conn.close()
        pg_conn.close()
        
        print(f"\n🎉 Migration completed!")
        print(f"📊 Total records migrated: {total_migrated}")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False

def verify_migration():
    """Verify migration results"""
    
    # Load production environment
    load_dotenv('.env.production')
    
    sqlite_path = 'instance/edubot_management.db'
    supabase_url = os.environ.get('DATABASE_URL')
    
    if supabase_url.startswith('postgres://'):
        supabase_url = supabase_url.replace('postgres://', 'postgresql://', 1)
    
    try:
        sqlite_conn = sqlite3.connect(sqlite_path)
        pg_conn = psycopg2.connect(supabase_url)
        
        sqlite_cursor = sqlite_conn.cursor()
        pg_cursor = pg_conn.cursor()
        
        # Get tables
        sqlite_cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        tables = [row[0] for row in sqlite_cursor.fetchall()]
        
        print("🔍 Migration Verification")
        print("=" * 50)
        print(f"{'Table':<25} {'SQLite':<8} {'Supabase':<10} {'Status':<10}")
        print("-" * 50)
        
        all_match = True
        for table in tables:
            try:
                # SQLite count
                sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                sqlite_count = sqlite_cursor.fetchone()[0]
                
                # Supabase count
                pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                supabase_count = pg_cursor.fetchone()[0]
                
                status = "✅ Match" if sqlite_count == supabase_count else "❌ Mismatch"
                if sqlite_count != supabase_count:
                    all_match = False
                
                print(f"{table:<25} {sqlite_count:<8} {supabase_count:<10} {status:<10}")
                
            except Exception as e:
                print(f"{table:<25} {'Error':<8} {'Error':<10} {'❌ Error':<10}")
                all_match = False
        
        print("-" * 50)
        if all_match:
            print("✅ All tables match! Migration successful!")
        else:
            print("⚠️  Some tables don't match. Check details above.")
        
        sqlite_conn.close()
        pg_conn.close()
        
        return all_match
        
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "migrate":
            migrate_data()
        elif command == "verify":
            verify_migration()
        else:
            print("Usage: python fixed_migration.py [migrate|verify]")
    else:
        print("Fixed SQLite to Supabase Migration")
        print("Usage: python fixed_migration.py [migrate|verify]")
        print("")
        print("Commands:")
        print("  migrate - Migrate data from SQLite to Supabase")
        print("  verify  - Verify migration results")
