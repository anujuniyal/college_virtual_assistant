#!/usr/bin/env python3
"""
Test Supabase Setup Script
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

def test_supabase_setup():
    """Test Supabase database setup"""
    
    # Load production environment
    load_dotenv('.env.production')
    
    supabase_url = os.environ.get('DATABASE_URL')
    
    if not supabase_url:
        print("❌ DATABASE_URL not found in .env.production")
        return False
    
    if supabase_url.startswith('postgres://'):
        supabase_url = supabase_url.replace('postgres://', 'postgresql://', 1)
    
    try:
        conn = psycopg2.connect(supabase_url)
        cursor = conn.cursor()
        
        print("🔍 Testing Supabase Database Setup")
        print("=" * 50)
        
        # Check if all expected tables exist
        expected_tables = [
            'admins', 'students', 'faculty', 'notifications', 'results',
            'fee_records', 'complaints', 'student_registrations',
            'telegram_user_mappings', 'otp_verifications', 'predefined_info',
            'faq_records', 'chatbot_qa', 'chatbot_unknown'
        ]
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 Expected tables: {len(expected_tables)}")
        print(f"📋 Found tables: {len(existing_tables)}")
        
        missing_tables = []
        for table in expected_tables:
            if table in existing_tables:
                print(f"   ✅ {table}")
            else:
                print(f"   ❌ {table} (missing)")
                missing_tables.append(table)
        
        # Check for indexes
        print("\n📊 Checking indexes...")
        cursor.execute("""
            SELECT indexname, tablename 
            FROM pg_indexes 
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname
        """)
        indexes = cursor.fetchall()
        
        print(f"   Found {len(indexes)} indexes")
        
        # Check for triggers
        print("\n⚡ Checking triggers...")
        cursor.execute("""
            SELECT trigger_name, event_manipulation, event_object_table
            FROM information_schema.triggers
            WHERE trigger_schema = 'public'
            ORDER BY event_object_table, trigger_name
        """)
        triggers = cursor.fetchall()
        
        print(f"   Found {len(triggers)} triggers")
        
        conn.close()
        
        if not missing_tables:
            print("\n✅ Supabase setup is complete!")
            return True
        else:
            print(f"\n⚠️  {len(missing_tables)} tables missing")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Supabase setup: {str(e)}")
        return False

if __name__ == "__main__":
    test_supabase_setup()
