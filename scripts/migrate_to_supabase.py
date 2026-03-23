#!/usr/bin/env python3
"""
Database Migration Script: SQLite to Supabase PostgreSQL
Migrates all data from local SQLite database to Supabase PostgreSQL
"""

import os
import sys
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseMigrator:
    def __init__(self):
        self.sqlite_path = 'instance/edubot_management.db'
        self.supabase_url = os.environ.get('DATABASE_URL')
        
        if not self.supabase_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        # Convert postgres:// to postgresql:// for psycopg2
        if self.supabase_url.startswith('postgres://'):
            self.supabase_url = self.supabase_url.replace('postgres://', 'postgresql://', 1)
    
    def get_sqlite_connection(self):
        """Get SQLite connection"""
        if not os.path.exists(self.sqlite_path):
            raise FileNotFoundError(f"SQLite database not found: {self.sqlite_path}")
        return sqlite3.connect(self.sqlite_path)
    
    def get_supabase_connection(self):
        """Get Supabase PostgreSQL connection"""
        return psycopg2.connect(self.supabase_url)
    
    def get_table_schema(self, conn, table_name):
        """Get table schema from SQLite"""
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        return {col[1]: col for col in columns}
    
    def migrate_table(self, sqlite_conn, pg_conn, table_name):
        """Migrate a single table from SQLite to PostgreSQL"""
        print(f"🔄 Migrating table: {table_name}")
        
        sqlite_cursor = sqlite_conn.cursor()
        pg_cursor = pg_conn.cursor()
        
        try:
            # Get data from SQLite
            sqlite_cursor.execute(f"SELECT * FROM {table_name}")
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                print(f"   ✅ No data to migrate in {table_name}")
                return
            
            # Get column names
            sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in sqlite_cursor.fetchall()]
            
            # Prepare insert query
            placeholders = ', '.join(['%s'] * len(columns))
            columns_str = ', '.join(columns)
            insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
            
            # Insert data into PostgreSQL
            migrated_count = 0
            for row in rows:
                try:
                    # Convert data types
                    converted_row = self.convert_row_data(row, table_name)
                    pg_cursor.execute(insert_query, converted_row)
                    migrated_count += 1
                except Exception as e:
                    print(f"   ⚠️  Error inserting row {row}: {str(e)}")
                    continue
            
            pg_conn.commit()
            print(f"   ✅ Migrated {migrated_count} rows from {table_name}")
            
        except Exception as e:
            pg_conn.rollback()
            print(f"   ❌ Error migrating {table_name}: {str(e)}")
            raise
    
    def convert_row_data(self, row, table_name):
        """Convert SQLite data to PostgreSQL compatible format"""
        converted = []
        
        for i, value in enumerate(row):
            if value is None:
                converted.append(None)
            elif isinstance(value, str):
                # Handle empty strings and special characters
                if value == '':
                    converted.append(None)
                else:
                    converted.append(value)
            elif isinstance(value, bytes):
                # Convert bytes to string (for BLOB data)
                try:
                    converted.append(value.decode('utf-8'))
                except:
                    converted.append(str(value))
            else:
                converted.append(value)
        
        return converted
    
    def create_postgresql_schema(self, pg_conn):
        """Create PostgreSQL schema if it doesn't exist"""
        print("🏗️  Creating PostgreSQL schema...")
        
        schema_sql = """
        -- Create extensions
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        
        -- Create indexes for better performance
        -- These will be created after data migration
        """
        
        cursor = pg_conn.cursor()
        try:
            cursor.execute(schema_sql)
            pg_conn.commit()
            print("   ✅ Schema created successfully")
        except Exception as e:
            pg_conn.rollback()
            print(f"   ⚠️  Schema creation warning: {str(e)}")
    
    def create_indexes(self, pg_conn):
        """Create performance indexes"""
        print("📊 Creating performance indexes...")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_admins_email ON admins(email);",
            "CREATE INDEX IF NOT EXISTS idx_students_roll_number ON students(roll_number);",
            "CREATE INDEX IF NOT EXISTS idx_faculty_email ON faculty(email);",
            "CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at);",
            "CREATE INDEX IF NOT EXISTS idx_results_roll_number ON results(roll_number);",
            "CREATE INDEX IF NOT EXISTS idx_fee_records_roll_number ON fee_records(roll_number);",
            "CREATE INDEX IF NOT EXISTS idx_complaints_created_at ON complaints(created_at);",
            "CREATE INDEX IF NOT EXISTS idx_student_registrations_created_at ON student_registrations(created_at);",
            "CREATE INDEX IF NOT EXISTS idx_telegram_user_mappings_telegram_id ON telegram_user_mappings(telegram_id);",
            "CREATE INDEX IF NOT EXISTS idx_otp_verifications_email ON otp_verifications(email);",
            "CREATE INDEX IF NOT EXISTS idx_otp_verifications_created_at ON otp_verifications(created_at);",
        ]
        
        cursor = pg_conn.cursor()
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except Exception as e:
                print(f"   ⚠️  Index creation warning: {str(e)}")
        
        pg_conn.commit()
        print("   ✅ Indexes created successfully")
    
    def get_all_tables(self, conn):
        """Get all table names from SQLite"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        return [row[0] for row in cursor.fetchall()]
    
    def reset_sequences(self, pg_conn):
        """Reset PostgreSQL sequences after migration"""
        print("🔄 Resetting sequences...")
        
        cursor = pg_conn.cursor()
        
        # Get all tables and their primary key columns
        tables_to_reset = [
            ('admins', 'id'),
            ('students', 'id'),
            ('faculty', 'id'),
            ('notifications', 'id'),
            ('results', 'id'),
            ('fee_records', 'id'),
            ('complaints', 'id'),
            ('student_registrations', 'id'),
            ('telegram_user_mappings', 'id'),
            ('otp_verifications', 'id'),
            ('predefined_info', 'id'),
            ('faq_records', 'id'),
            ('chatbot_qa', 'id'),
            ('chatbot_unknown', 'id'),
        ]
        
        for table_name, pk_column in tables_to_reset:
            try:
                # Get max ID from table
                cursor.execute(f"SELECT MAX({pk_column}) FROM {table_name}")
                max_id = cursor.fetchone()[0]
                
                if max_id:
                    # Reset sequence to max_id + 1
                    sequence_name = f"{table_name}_{pk_column}_seq"
                    cursor.execute(f"""
                        SELECT setval(pg_get_serial_sequence('{table_name}', '{pk_column}'), 
                                      COALESCE(MAX({pk_column}), 1), 
                                      MAX({pk_column}) IS NOT NULL) 
                        FROM {table_name}
                    """)
                    print(f"   ✅ Reset sequence for {table_name} to {max_id + 1}")
                
            except Exception as e:
                print(f"   ⚠️  Sequence reset warning for {table_name}: {str(e)}")
        
        pg_conn.commit()
    
    def migrate_all_data(self):
        """Perform complete migration"""
        print("🚀 Starting database migration from SQLite to Supabase PostgreSQL")
        print("=" * 60)
        
        try:
            # Connect to databases
            sqlite_conn = self.get_sqlite_connection()
            pg_conn = self.get_supabase_connection()
            
            # Get all tables
            tables = self.get_all_tables(sqlite_conn)
            print(f"📋 Found {len(tables)} tables to migrate: {', '.join(tables)}")
            
            # Create PostgreSQL schema
            self.create_postgresql_schema(pg_conn)
            
            # Migrate each table
            for table in tables:
                self.migrate_table(sqlite_conn, pg_conn, table)
            
            # Create indexes
            self.create_indexes(pg_conn)
            
            # Reset sequences
            self.reset_sequences(pg_conn)
            
            # Close connections
            sqlite_conn.close()
            pg_conn.close()
            
            print("=" * 60)
            print("✅ Migration completed successfully!")
            print("🎉 Your Supabase database is now ready for production!")
            
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            sys.exit(1)
    
    def verify_migration(self):
        """Verify migration by comparing record counts"""
        print("🔍 Verifying migration...")
        
        try:
            sqlite_conn = self.get_sqlite_connection()
            pg_conn = self.get_supabase_connection()
            
            tables = self.get_all_tables(sqlite_conn)
            
            print(f"{'Table':<25} {'SQLite':<10} {'PostgreSQL':<12} {'Status':<10}")
            print("-" * 60)
            
            all_match = True
            for table in tables:
                # Get SQLite count
                sqlite_cursor = sqlite_conn.cursor()
                sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                sqlite_count = sqlite_cursor.fetchone()[0]
                
                # Get PostgreSQL count
                pg_cursor = pg_conn.cursor()
                try:
                    pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    pg_count = pg_cursor.fetchone()[0]
                    status = "✅ Match" if sqlite_count == pg_count else "❌ Mismatch"
                    if sqlite_count != pg_count:
                        all_match = False
                except Exception:
                    pg_count = "Error"
                    status = "❌ Error"
                    all_match = False
                
                print(f"{table:<25} {sqlite_count:<10} {pg_count:<12} {status:<10}")
            
            sqlite_conn.close()
            pg_conn.close()
            
            print("-" * 60)
            if all_match:
                print("✅ All tables verified successfully!")
            else:
                print("⚠️  Some tables have mismatches. Please check the details above.")
            
        except Exception as e:
            print(f"❌ Verification failed: {str(e)}")

def main():
    """Main migration function"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        migrator = DatabaseMigrator()
        
        if command == "migrate":
            migrator.migrate_all_data()
        elif command == "verify":
            migrator.verify_migration()
        elif command == "full":
            migrator.migrate_all_data()
            migrator.verify_migration()
        else:
            print("Usage: python migrate_to_supabase.py [migrate|verify|full]")
    else:
        print("SQLite to Supabase Migration Tool")
        print("Usage: python migrate_to_supabase.py [migrate|verify|full]")
        print("")
        print("Commands:")
        print("  migrate - Migrate data from SQLite to Supabase")
        print("  verify  - Verify migration by comparing record counts")
        print("  full    - Migrate and verify in one step")

if __name__ == "__main__":
    main()
