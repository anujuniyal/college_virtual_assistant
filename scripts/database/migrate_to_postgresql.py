#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script
This script helps migrate existing SQLite data to PostgreSQL for deployment
"""

import os
import sys
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import psycopg2
        print("✅ psycopg2 is installed")
        return True
    except ImportError:
        print("❌ psycopg2 is not installed")
        print("Please install it with: pip install psycopg2-binary")
        return False


def check_sqlite_database():
    """Check if SQLite database exists and has data"""
    sqlite_path = 'edubot_management.db'
    
    if not os.path.exists(sqlite_path):
        print("❌ SQLite database not found")
        return False
    
    try:
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        
        # Check if there are tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("❌ SQLite database is empty")
            conn.close()
            return False
        
        # Count total records
        total_records = 0
        for table_name, in tables:
            if table_name != 'sqlite_sequence':
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                total_records += count
        
        conn.close()
        
        print(f"✅ SQLite database found with {len(tables)} tables and {total_records} records")
        return True
        
    except Exception as e:
        print(f"❌ Error checking SQLite database: {str(e)}")
        return False


def get_postgresql_connection_string():
    """Get PostgreSQL connection string from user input or environment"""
    # Check if DATABASE_URL is set
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        print(f"✅ Found DATABASE_URL in environment")
        return database_url
    
    # Prompt user for connection details
    print("\n📝 Enter PostgreSQL connection details:")
    host = input("Host (default: localhost): ").strip() or "localhost"
    port = input("Port (default: 5432): ").strip() or "5432"
    database = input("Database name (default: edubot): ").strip() or "edubot"
    username = input("Username (default: postgres): ").strip() or "postgres"
    password = input("Password: ").strip()
    
    if not password:
        print("❌ Password is required")
        return None
    
    return f"postgresql://{username}:{password}@{host}:{port}/{database}"


def test_postgresql_connection(connection_string):
    """Test PostgreSQL connection"""
    try:
        import psycopg2
        
        print("🔍 Testing PostgreSQL connection...")
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        conn.close()
        
        print(f"✅ PostgreSQL connection successful")
        print(f"   Version: {version.split(',')[0]}")
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {str(e)}")
        return False


def backup_sqlite_database():
    """Create a backup of the SQLite database"""
    sqlite_path = 'edubot_management.db'
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{sqlite_path}.backup_{timestamp}"
    
    try:
        import shutil
        shutil.copy2(sqlite_path, backup_path)
        print(f"✅ SQLite database backed up to: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Backup failed: {str(e)}")
        return None


def run_migration(connection_string):
    """Run the migration using the database manager"""
    try:
        print("🔄 Starting migration...")
        
        # Set environment variable for the migration
        env = os.environ.copy()
        env['DATABASE_URL'] = connection_string
        
        # Run the database manager with migrate command
        result = subprocess.run(
            [sys.executable, 'database_manager.py', 'migrate'],
            env=env,
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        if result.returncode == 0:
            print("✅ Migration completed successfully")
            print(result.stdout)
            return True
        else:
            print("❌ Migration failed")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Migration error: {str(e)}")
        return False


def verify_migration():
    """Verify that migration was successful"""
    try:
        print("🔍 Verifying migration...")
        
        # Test connection to PostgreSQL
        result = subprocess.run(
            [sys.executable, 'database_manager.py', 'test'],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        if result.returncode == 0:
            print("✅ Migration verification successful")
            print(result.stdout)
            return True
        else:
            print("❌ Migration verification failed")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Verification error: {str(e)}")
        return False


def main():
    """Main migration function"""
    print("🚀 SQLite to PostgreSQL Migration Tool")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check SQLite database
    if not check_sqlite_database():
        print("\n💡 Make sure you have a local SQLite database with data before migrating.")
        sys.exit(1)
    
    # Get PostgreSQL connection string
    connection_string = get_postgresql_connection_string()
    if not connection_string:
        sys.exit(1)
    
    # Test PostgreSQL connection
    if not test_postgresql_connection(connection_string):
        print("\n💡 Please check your PostgreSQL connection details and ensure the database exists.")
        sys.exit(1)
    
    # Backup SQLite database
    print("\n📦 Creating backup of SQLite database...")
    backup_path = backup_sqlite_database()
    if not backup_path:
        sys.exit(1)
    
    # Confirm migration
    print(f"\n⚠️  Ready to migrate SQLite data to PostgreSQL.")
    print(f"   Backup will be saved to: {backup_path}")
    confirm = input("Continue with migration? (y/N): ").strip().lower()
    
    if confirm != 'y':
        print("❌ Migration cancelled")
        sys.exit(0)
    
    # Run migration
    print("\n🔄 Running migration...")
    if not run_migration(connection_string):
        print("\n❌ Migration failed. Your original SQLite database is unchanged.")
        print(f"   Backup is available at: {backup_path}")
        sys.exit(1)
    
    # Verify migration
    print("\n🔍 Verifying migration...")
    if not verify_migration():
        print("\n⚠️  Migration completed but verification failed.")
        print("   Please check your PostgreSQL database manually.")
        sys.exit(1)
    
    print("\n🎉 Migration completed successfully!")
    print(f"   Your data has been migrated to PostgreSQL.")
    print(f"   SQLite backup is available at: {backup_path}")
    print(f"   You can now deploy to Render with the migrated data.")


if __name__ == '__main__':
    main()
