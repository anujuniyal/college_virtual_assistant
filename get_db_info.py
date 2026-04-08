#!/usr/bin/env python3
"""
Get Database Information
"""
from app import create_app
from app.extensions import db
import os

def main():
    """Get database name and location"""
    app = create_app()
    app.app_context().push()
    
    print("=== DATABASE INFORMATION ===")
    
    # Database name/type
    db_uri = app.config["SQLALCHEMY_DATABASE_URI"]
    if "sqlite" in db_uri.lower():
        db_name = "SQLite"
        print(f"Database Name: {db_name}")
    else:
        db_name = "Other Database"
        print(f"Database Name: {db_name}")
    
    # Database engine
    print(f"Database Engine: {db.engine}")
    
    # Database URI
    print(f"Database URI: {db_uri}")
    
    # Database file location and details
    if "sqlite" in db_uri.lower():
        db_path = db_uri.replace('sqlite:///', '')
        full_path = os.path.abspath(db_path)
        print(f"Database File Location: {full_path}")
        print(f"Database File Exists: {os.path.exists(full_path)}")
        
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            print(f"Database File Size: {size:,} bytes ({size/1024:.1f} KB)")
            
            # Get file modification time
            mtime = os.path.getmtime(full_path)
            import datetime
            mod_time = datetime.datetime.fromtimestamp(mtime)
            print(f"Last Modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Check if file is writable
            if os.access(full_path, os.W_OK):
                print("Database File Access: Read/Write ✅")
            else:
                print("Database File Access: Read only ⚠️")
        else:
            print("Database File Access: Not found ❌")
    else:
        print("Database Type: Non-SQLite database")
        print("Database Location: Configured in application")

if __name__ == '__main__':
    main()
