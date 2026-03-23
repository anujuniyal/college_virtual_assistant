#!/usr/bin/env python3
"""
Fix Missing Tables in Supabase
Creates the missing otp_verifications and chatbot_unknown tables
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

def fix_missing_tables():
    """Create missing tables in Supabase"""
    
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
        
        print("🔧 Fixing Missing Tables in Supabase")
        print("=" * 50)
        
        # Create otp_verifications table
        print("📋 Creating otp_verifications table...")
        otp_table_sql = """
        CREATE TABLE IF NOT EXISTS otp_verifications (
            id SERIAL PRIMARY KEY,
            email VARCHAR(120) NOT NULL,
            otp VARCHAR(10) NOT NULL,
            purpose VARCHAR(20) DEFAULT 'login',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            is_used BOOLEAN DEFAULT FALSE
        );
        """
        cursor.execute(otp_table_sql)
        print("   ✅ otp_verifications table created")
        
        # Create chatbot_unknown table
        print("📋 Creating chatbot_unknown table...")
        unknown_table_sql = """
        CREATE TABLE IF NOT EXISTS chatbot_unknown (
            id SERIAL PRIMARY KEY,
            question TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        cursor.execute(unknown_table_sql)
        print("   ✅ chatbot_unknown table created")
        
        # Add indexes for otp_verifications
        print("📊 Adding indexes for otp_verifications...")
        otp_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_otp_verifications_email ON otp_verifications(email);",
            "CREATE INDEX IF NOT EXISTS idx_otp_verifications_created_at ON otp_verifications(created_at);",
            "CREATE INDEX IF NOT EXISTS idx_otp_verifications_expires_at ON otp_verifications(expires_at);",
            "CREATE INDEX IF NOT EXISTS idx_otp_verifications_is_used ON otp_verifications(is_used);"
        ]
        
        for index_sql in otp_indexes:
            cursor.execute(index_sql)
        print("   ✅ otp_verifications indexes created")
        
        # Add indexes for chatbot_unknown
        print("📊 Adding indexes for chatbot_unknown...")
        unknown_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_chatbot_unknown_created_at ON chatbot_unknown(created_at);"
        ]
        
        for index_sql in unknown_indexes:
            cursor.execute(index_sql)
        print("   ✅ chatbot_unknown indexes created")
        
        # Verify tables were created
        print("🔍 Verifying table creation...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('otp_verifications', 'chatbot_unknown')
            ORDER BY table_name
        """)
        created_tables = [row[0] for row in cursor.fetchall()]
        
        print(f"   📋 Created tables: {created_tables}")
        
        conn.commit()
        conn.close()
        
        if len(created_tables) == 2:
            print("\n✅ All missing tables created successfully!")
            return True
        else:
            print(f"\n⚠️  Only {len(created_tables)} tables created")
            return False
            
    except Exception as e:
        print(f"❌ Error creating missing tables: {str(e)}")
        return False

if __name__ == "__main__":
    fix_missing_tables()
