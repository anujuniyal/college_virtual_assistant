#!/usr/bin/env python3
"""
Check Supabase Database Content
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

def check_supabase():
    """Check what's in Supabase database"""
    
    # Load production environment
    load_dotenv('.env.production')
    
    supabase_url = os.environ.get('DATABASE_URL')
    
    if not supabase_url:
        print("❌ DATABASE_URL not found in .env.production")
        return
    
    if supabase_url.startswith('postgres://'):
        supabase_url = supabase_url.replace('postgres://', 'postgresql://', 1)
    
    try:
        pg_conn = psycopg2.connect(supabase_url)
        pg_cursor = pg_conn.cursor()
        
        print("🔍 Checking Supabase Database Content")
        print("=" * 50)
        
        # Get all tables
        pg_cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tables = [row[0] for row in pg_cursor.fetchall()]
        
        print(f"📋 Found {len(tables)} tables in Supabase:")
        print(f"{'Table':<25} {'Records':<10}")
        print("-" * 35)
        
        total_records = 0
        for table in tables:
            try:
                pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = pg_cursor.fetchone()[0]
                print(f"{table:<25} {count:<10}")
                total_records += count
            except Exception as e:
                print(f"{table:<25} {'Error':<10}")
        
        print("-" * 35)
        print(f"Total records: {total_records}")
        
        # Show some sample data
        print("\n📄 Sample Data:")
        print("=" * 50)
        
        sample_tables = ['admins', 'students', 'notifications', 'faculty', 'chatbot_qa']
        
        for table in sample_tables:
            try:
                pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = pg_cursor.fetchone()[0]
                
                if count > 0:
                    print(f"\n📊 {table} ({count} records):")
                    
                    if table == 'admins':
                        pg_cursor.execute(f"SELECT id, username, email, role FROM {table} LIMIT 3")
                    elif table == 'students':
                        pg_cursor.execute(f"SELECT id, name, roll_number, email FROM {table} LIMIT 3")
                    elif table == 'notifications':
                        pg_cursor.execute(f"SELECT id, title, created_at FROM {table} LIMIT 3")
                    elif table == 'faculty':
                        pg_cursor.execute(f"SELECT id, name, email, role FROM {table} LIMIT 3")
                    elif table == 'chatbot_qa':
                        pg_cursor.execute(f"SELECT id, question, answer FROM {table} LIMIT 3")
                    
                    rows = pg_cursor.fetchall()
                    for row in rows:
                        print(f"   {row}")
                
            except Exception as e:
                print(f"❌ Error checking {table}: {str(e)}")
        
        pg_conn.close()
        
        print("\n✅ Supabase database check completed!")
        
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {str(e)}")

if __name__ == "__main__":
    check_supabase()
