#!/usr/bin/env python3
"""
Force PostgreSQL connection in production
This script overrides any SQLite fallback and ensures PostgreSQL is used
"""

import os
import sys

def force_postgresql_connection():
    """Force PostgreSQL connection in production"""
    # Set production environment
    os.environ['FLASK_ENV'] = 'production'
    
    # Force DATABASE_URL if not set (using Render's expected format)
    if not os.environ.get('DATABASE_URL'):
        # Try to get from Render's database service
        database_url = os.environ.get('POSTGRESQL_URL') or os.environ.get('DATABASE_URL_RENDER')
        
        if database_url:
            os.environ['DATABASE_URL'] = database_url
            print(f"✅ Forced DATABASE_URL: {database_url[:50]}...")
        else:
            # Use the Supabase URL from .env.render as fallback
            supabase_url = "postgresql://postgres:anujajuniyal007@db.sqzpzxcmhgkbvjfuxgsk.supabase.co:5432/postgres"
            os.environ['DATABASE_URL'] = supabase_url
            print(f"✅ Using Supabase fallback: {supabase_url[:50]}...")
    
    # Test the connection
    try:
        from app import create_app, db
        app = create_app()
        
        with app.app_context():
            db.session.execute("SELECT 1")
            print("✅ PostgreSQL connection test successful")
            return True
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {str(e)}")
        return False

if __name__ == '__main__':
    success = force_postgresql_connection()
    sys.exit(0 if success else 1)
