#!/usr/bin/env python3
"""
Local SQLite to Supabase Migration Script
Migrates data from local SQLite database to Supabase PostgreSQL
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

class LocalToSupabaseMigrator:
    def __init__(self):
        self.sqlite_path = 'instance/edubot_management.db'
        self.supabase_url = os.environ.get('SUPABASE_DATABASE_URL') or os.environ.get('DATABASE_URL')
        
        # For migration, we need the Supabase URL specifically
        if not self.supabase_url or self.supabase_url.startswith('sqlite'):
            # Try to get from production env file
            prod_env_path = '.env.production'
            if os.path.exists(prod_env_path):
                load_dotenv(prod_env_path)
                self.supabase_url = os.environ.get('DATABASE_URL')
        
        if not self.supabase_url or self.supabase_url.startswith('sqlite'):
            raise ValueError("Supabase DATABASE_URL not found or still pointing to SQLite")
        
        # Convert postgres:// to postgresql:// for psycopg2
        if self.supabase_url.startswith('postgres://'):
            self.supabase_url = self.supabase_url.replace('postgres://', 'postgresql://', 1)
        
        print(f"🔗 Using Supabase URL: {self.supabase_url.split('@')[0]}@{self.supabase_url.split('@')[1]}")
    
    def get_sqlite_connection(self):
        """Get SQLite connection"""
        if not os.path.exists(self.sqlite_path):
            raise FileNotFoundError(f"SQLite database not found: {self.sqlite_path}")
        return sqlite3.connect(self.sqlite_path)
    
    def get_supabase_connection(self):
        """Get Supabase PostgreSQL connection"""
        try:
            return psycopg2.connect(self.supabase_url)
        except Exception as e:
            print(f"❌ Failed to connect to Supabase: {str(e)}")
            print("🔧 Please check your Supabase DATABASE_URL in .env.production")
            raise
    
    def check_sqlite_data(self):
        """Check if SQLite database has data"""
        conn = self.get_sqlite_connection()
        cursor = conn.cursor()
        
        tables_with_data = {}
        
        # Get all tables
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                if count > 0:
                    tables_with_data[table] = count
            except Exception as e:
                print(f"⚠️  Could not check table {table}: {str(e)}")
        
        conn.close()
        
        return tables_with_data
    
    def setup_supabase_tables(self):
        """Setup Supabase tables if they don't exist"""
        print("🏗️  Setting up Supabase tables...")
        
        try:
            result = os.system("python scripts/setup_supabase.py setup")
            if result == 0:
                print("   ✅ Supabase tables setup completed")
                return True
            else:
                print("   ❌ Supabase tables setup failed")
                return False
        except Exception as e:
            print(f"   ❌ Error setting up Supabase tables: {str(e)}")
            return False
    
    def migrate_table_data(self, sqlite_conn, pg_conn, table_name):
        """Migrate data for a specific table"""
        print(f"📊 Migrating {table_name}...")
        
        sqlite_cursor = sqlite_conn.cursor()
        pg_cursor = pg_conn.cursor()
        
        try:
            # Get data from SQLite
            sqlite_cursor.execute(f"SELECT * FROM {table_name}")
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                print(f"   ✅ No data in {table_name}")
                return True, 0
            
            # Get column names
            sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in sqlite_cursor.fetchall()]
            
            # Prepare insert query
            placeholders = ', '.join(['%s'] * len(columns))
            columns_str = ', '.join(columns)
            insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
            
            # Clear existing data in Supabase table
            pg_cursor.execute(f"DELETE FROM {table_name}")
            
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
            return True, migrated_count
            
        except Exception as e:
            pg_conn.rollback()
            print(f"   ❌ Error migrating {table_name}: {str(e)}")
            return False, 0
    
    def convert_row_data(self, row, table_name):
        """Convert SQLite data to PostgreSQL compatible format"""
        converted = []
        
        for i, value in enumerate(row):
            if value is None:
                converted.append(None)
            elif isinstance(value, str):
                # Handle empty strings
                if value == '':
                    converted.append(None)
                else:
                    converted.append(value)
            elif isinstance(value, bytes):
                # Convert bytes to string
                try:
                    converted.append(value.decode('utf-8'))
                except:
                    converted.append(str(value))
            else:
                converted.append(value)
        
        return converted
    
    def reset_sequences(self, pg_conn):
        """Reset PostgreSQL sequences after migration"""
        print("🔄 Resetting sequences...")
        
        cursor = pg_conn.cursor()
        
        tables_with_sequences = [
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
        
        for table_name, pk_column in tables_with_sequences:
            try:
                cursor.execute(f"SELECT MAX({pk_column}) FROM {table_name}")
                result = cursor.fetchone()
                max_id = result[0] if result and result[0] is not None else 0
                
                if max_id > 0:
                    sequence_name = f"{table_name}_{pk_column}_seq"
                    cursor.execute(f"""
                        SELECT setval(pg_get_serial_sequence('{table_name}', '{pk_column}'), 
                                      {max_id}, true)
                    """)
                    print(f"   ✅ Reset {table_name} sequence to {max_id}")
                
            except Exception as e:
                print(f"   ⚠️  Sequence reset warning for {table_name}: {str(e)}")
        
        pg_conn.commit()
    
    def verify_migration(self):
        """Verify migration by comparing record counts"""
        print("🔍 Verifying migration...")
        
        sqlite_conn = self.get_sqlite_connection()
        pg_conn = self.get_supabase_connection()
        
        sqlite_cursor = sqlite_conn.cursor()
        pg_cursor = pg_conn.cursor()
        
        # Get all tables
        sqlite_cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        tables = [row[0] for row in sqlite_cursor.fetchall()]
        
        print(f"{'Table':<25} {'SQLite':<8} {'Supabase':<10} {'Status':<10}")
        print("-" * 60)
        
        all_match = True
        for table in tables:
            try:
                # Get SQLite count
                sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                sqlite_count = sqlite_cursor.fetchone()[0]
                
                # Get PostgreSQL count
                pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                pg_count = pg_cursor.fetchone()[0]
                
                status = "✅ Match" if sqlite_count == pg_count else "❌ Mismatch"
                if sqlite_count != pg_count:
                    all_match = False
                
                print(f"{table:<25} {sqlite_count:<8} {pg_count:<10} {status:<10}")
                
            except Exception as e:
                print(f"{table:<25} {'Error':<8} {'Error':<10} {'❌ Error':<10}")
                all_match = False
        
        sqlite_conn.close()
        pg_conn.close()
        
        print("-" * 60)
        if all_match:
            print("✅ All tables verified successfully!")
        else:
            print("⚠️  Some tables have mismatches. Please check the details above.")
        
        return all_match
    
    def run_migration(self):
        """Run complete migration process"""
        print("🚀 Starting Local SQLite to Supabase Migration")
        print("=" * 60)
        
        try:
            # Check SQLite data
            print("📋 Checking SQLite database...")
            tables_with_data = self.check_sqlite_data()
            
            if not tables_with_data:
                print("❌ No data found in SQLite database")
                return False
            
            print(f"   Found {len(tables_with_data)} tables with data:")
            for table, count in tables_with_data.items():
                print(f"   - {table}: {count} records")
            
            # Setup Supabase tables
            if not self.setup_supabase_tables():
                print("❌ Failed to setup Supabase tables")
                return False
            
            # Get connections
            sqlite_conn = self.get_sqlite_connection()
            pg_conn = self.get_supabase_connection()
            
            # Migrate each table
            total_migrated = 0
            successful_tables = 0
            
            for table_name in tables_with_data.keys():
                success, count = self.migrate_table_data(sqlite_conn, pg_conn, table_name)
                if success:
                    successful_tables += 1
                    total_migrated += count
            
            # Reset sequences
            self.reset_sequences(pg_conn)
            
            # Close connections
            sqlite_conn.close()
            pg_conn.close()
            
            # Verify migration
            print("\n" + "=" * 60)
            print("📊 Migration Summary:")
            print(f"   Tables processed: {successful_tables}/{len(tables_with_data)}")
            print(f"   Total records migrated: {total_migrated}")
            
            # Run verification
            self.verify_migration()
            
            print("=" * 60)
            print("✅ Migration completed successfully!")
            print("🎉 Your SQLite data is now available in Supabase!")
            
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            return False

def main():
    """Main migration function"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        migrator = LocalToSupabaseMigrator()
        
        if command == "migrate":
            migrator.run_migration()
        elif command == "verify":
            migrator.verify_migration()
        elif command == "check":
            tables = migrator.check_sqlite_data()
            print(f"Found {len(tables)} tables with data:")
            for table, count in tables.items():
                print(f"  - {table}: {count} records")
        else:
            print("Usage: python migrate_local_to_supabase.py [migrate|verify|check]")
    else:
        print("Local SQLite to Supabase Migration Tool")
        print("Usage: python migrate_local_to_supabase.py [migrate|verify|check]")
        print("")
        print("Commands:")
        print("  migrate - Migrate data from SQLite to Supabase")
        print("  verify  - Verify migration by comparing record counts")
        print("  check   - Check what data exists in SQLite")

if __name__ == "__main__":
    main()
