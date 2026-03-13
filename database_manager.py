#!/usr/bin/env python3
"""
Database Migration and Initialization Script
Handles migration from SQLite to PostgreSQL and proper initialization
"""

import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.factory import create_app
from app.config import Config

# Try to import psycopg2, but don't fail if it's not available
try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False


class DatabaseManager:
    """Manages database operations for dual SQLite/PostgreSQL setup"""
    
    def __init__(self):
        self.app = create_app()
        self.sqlite_path = 'edubot_management.db'
        
    def detect_database_type(self):
        """Detect which database type is being used"""
        with self.app.app_context():
            db_uri = self.app.config.get('SQLALCHEMY_DATABASE_URI', '')
            
            if db_uri.startswith('postgresql://'):
                return 'postgresql'
            elif db_uri.startswith('sqlite://'):
                return 'sqlite'
            else:
                return 'unknown'
    
    def get_database_info(self):
        """Get current database information"""
        db_type = self.detect_database_type()
        
        info = {
            'type': db_type,
            'uri': self.app.config.get('SQLALCHEMY_DATABASE_URI', ''),
            'environment': os.environ.get('FLASK_ENV', 'development'),
            'has_database_url': bool(os.environ.get('DATABASE_URL'))
        }
        
        if db_type == 'sqlite':
            info['sqlite_file'] = self.sqlite_path
            info['sqlite_exists'] = os.path.exists(self.sqlite_path)
            if info['sqlite_exists']:
                info['sqlite_size'] = os.path.getsize(self.sqlite_path)
        
        return info
    
    def initialize_database(self):
        """Initialize database with proper schema and data"""
        try:
            with self.app.app_context():
                from app.services.database_setup import DatabaseSetup
                
                print(f"🔧 Initializing {self.detect_database_type()} database...")
                
                # Initialize database using existing service
                success = DatabaseSetup.initialize_database()
                
                if success:
                    print(f"✅ Database initialized successfully")
                    return True
                else:
                    print(f"❌ Database initialization failed")
                    return False
                    
        except Exception as e:
            print(f"❌ Error initializing database: {str(e)}")
            return False
    
    def migrate_sqlite_to_postgresql(self, postgres_uri=None):
        """Migrate data from SQLite to PostgreSQL"""
        if not PSYCOPG2_AVAILABLE:
            print("❌ psycopg2 is not installed. Please install it with: pip install psycopg2-binary")
            return False
            
        if not os.path.exists(self.sqlite_path):
            print("❌ SQLite database not found. Nothing to migrate.")
            return False
        
        if not postgres_uri:
            postgres_uri = os.environ.get('DATABASE_URL')
            if not postgres_uri:
                print("❌ PostgreSQL URI not provided. Set DATABASE_URL environment variable.")
                return False
        
        try:
            print("🔄 Starting migration from SQLite to PostgreSQL...")
            
            # Connect to SQLite
            sqlite_conn = sqlite3.connect(self.sqlite_path)
            sqlite_cursor = sqlite_conn.cursor()
            
            # Connect to PostgreSQL
            if postgres_uri.startswith('postgres://'):
                postgres_uri = postgres_uri.replace('postgres://', 'postgresql://', 1)
            
            pg_conn = psycopg2.connect(postgres_uri)
            pg_cursor = pg_conn.cursor()
            
            # Get all tables from SQLite
            sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = sqlite_cursor.fetchall()
            
            print(f"📊 Found {len(tables)} tables to migrate")
            
            migrated_tables = 0
            for table_name, in tables:
                if table_name == 'sqlite_sequence':
                    continue  # Skip SQLite internal table
                
                try:
                    print(f"🔄 Migrating table: {table_name}")
                    
                    # Get table schema from SQLite
                    sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = sqlite_cursor.fetchall()
                    
                    # Create table in PostgreSQL (simplified)
                    column_defs = []
                    for col in columns:
                        col_name, col_type, not_null, default, pk = col
                        pg_type = self._convert_sqlite_type_to_postgresql(col_type)
                        col_def = f"{col_name} {pg_type}"
                        if not_null:
                            col_def += " NOT NULL"
                        if default:
                            col_def += f" DEFAULT {default}"
                        if pk:
                            col_def += " PRIMARY KEY"
                        column_defs.append(col_def)
                    
                    create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_defs)})"
                    pg_cursor.execute(create_table_sql)
                    
                    # Get data from SQLite
                    sqlite_cursor.execute(f"SELECT * FROM {table_name}")
                    rows = sqlite_cursor.fetchall()
                    
                    if rows:
                        # Get column names
                        column_names = [col[0] for col in columns]
                        placeholders = ', '.join(['%s'] * len(column_names))
                        insert_sql = f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({placeholders})"
                        
                        # Insert data into PostgreSQL
                        pg_cursor.executemany(insert_sql, rows)
                    
                    migrated_tables += 1
                    print(f"✅ Migrated {len(rows)} rows from {table_name}")
                    
                except Exception as e:
                    print(f"⚠️  Error migrating table {table_name}: {str(e)}")
                    continue
            
            # Commit changes
            pg_conn.commit()
            
            # Close connections
            sqlite_conn.close()
            pg_conn.close()
            
            print(f"✅ Migration completed. {migrated_tables}/{len(tables)} tables migrated.")
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            return False
    
    def _convert_sqlite_type_to_postgresql(self, sqlite_type):
        """Convert SQLite data types to PostgreSQL types"""
        sqlite_type = sqlite_type.upper()
        
        if 'INTEGER' in sqlite_type and 'PRIMARY KEY' in sqlite_type:
            return 'SERIAL PRIMARY KEY'
        elif 'INTEGER' in sqlite_type:
            return 'INTEGER'
        elif 'TEXT' in sqlite_type:
            return 'TEXT'
        elif 'REAL' in sqlite_type or 'FLOAT' in sqlite_type:
            return 'REAL'
        elif 'BOOLEAN' in sqlite_type:
            return 'BOOLEAN'
        elif 'BLOB' in sqlite_type:
            return 'BYTEA'
        else:
            return 'TEXT'
    
    def backup_sqlite_database(self):
        """Create a backup of the SQLite database"""
        if not os.path.exists(self.sqlite_path):
            print("❌ SQLite database not found")
            return False
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.sqlite_path}.backup_{timestamp}"
            
            import shutil
            shutil.copy2(self.sqlite_path, backup_path)
            
            print(f"✅ SQLite database backed up to: {backup_path}")
            return backup_path
            
        except Exception as e:
            print(f"❌ Backup failed: {str(e)}")
            return False
    
    def test_database_connection(self):
        """Test database connection"""
        try:
            with self.app.app_context():
                from app.extensions import db
                from sqlalchemy import text
                
                # Test connection
                db.session.execute(text('SELECT 1'))
                
                db_type = self.detect_database_type()
                print(f"✅ Database connection successful ({db_type})")
                return True
                
        except Exception as e:
            print(f"❌ Database connection failed: {str(e)}")
            return False


def main():
    """Main function for database management"""
    manager = DatabaseManager()
    
    print("🗄️  Database Management Tool")
    print("=" * 50)
    
    # Show current database info
    info = manager.get_database_info()
    print(f"Database Type: {info['type']}")
    print(f"Environment: {info['environment']}")
    print(f"Has DATABASE_URL: {info['has_database_url']}")
    
    if info['type'] == 'sqlite':
        print(f"SQLite File: {info['sqlite_file']}")
        print(f"SQLite Exists: {info['sqlite_exists']}")
        if info.get('sqlite_exists'):
            print(f"SQLite Size: {info['sqlite_size']} bytes")
    
    print()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'init':
            success = manager.initialize_database()
            sys.exit(0 if success else 1)
            
        elif command == 'test':
            success = manager.test_database_connection()
            sys.exit(0 if success else 1)
            
        elif command == 'migrate':
            # Backup SQLite before migration
            backup_path = manager.backup_sqlite_database()
            if backup_path:
                success = manager.migrate_sqlite_to_postgresql()
                sys.exit(0 if success else 1)
            else:
                sys.exit(1)
                
        elif command == 'backup':
            backup_path = manager.backup_sqlite_database()
            sys.exit(0 if backup_path else 1)
            
        elif command == 'info':
            # Info already shown above
            sys.exit(0)
            
        else:
            print(f"❌ Unknown command: {command}")
            print_usage()
            sys.exit(1)
    else:
        # Default behavior: initialize database
        success = manager.initialize_database()
        sys.exit(0 if success else 1)


def print_usage():
    """Print usage information"""
    print("\nUsage:")
    print("  python database_manager.py [command]")
    print("\nCommands:")
    print("  init     - Initialize database (default)")
    print("  test     - Test database connection")
    print("  migrate  - Migrate from SQLite to PostgreSQL")
    print("  backup   - Backup SQLite database")
    print("  info     - Show database information")


if __name__ == '__main__':
    main()
