#!/usr/bin/env python3
"""
Add Triggers to Supabase
Creates triggers for updated_at timestamps
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

def add_triggers():
    """Add triggers to Supabase tables"""
    
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
        
        print("⚡ Adding Triggers to Supabase")
        print("=" * 50)
        
        # Create the update function
        print("🔧 Creating update_updated_at_column function...")
        function_sql = """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        """
        cursor.execute(function_sql)
        print("   ✅ Function created")
        
        # Tables that need updated_at triggers
        tables_with_updated_at = [
            'admins',
            'students', 
            'faculty',
            'fee_records',
            'complaints',
            'student_registrations',
            'telegram_user_mappings',
            'predefined_info',
            'faq_records',
            'chatbot_qa'
        ]
        
        # Create triggers for each table
        for table in tables_with_updated_at:
            print(f"⚡ Creating trigger for {table}...")
            trigger_sql = f"""
            CREATE TRIGGER update_{table}_updated_at 
                BEFORE UPDATE ON {table} 
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            """
            
            try:
                cursor.execute(trigger_sql)
                print(f"   ✅ Trigger for {table} created")
            except Exception as e:
                if "already exists" in str(e):
                    print(f"   ⚠️  Trigger for {table} already exists")
                else:
                    print(f"   ❌ Error creating trigger for {table}: {str(e)}")
        
        # Verify triggers were created
        print("\n🔍 Verifying trigger creation...")
        cursor.execute("""
            SELECT trigger_name, event_object_table
            FROM information_schema.triggers
            WHERE trigger_schema = 'public'
            ORDER BY event_object_table, trigger_name
        """)
        triggers = cursor.fetchall()
        
        print(f"   📋 Found {len(triggers)} triggers:")
        for trigger_name, table_name in triggers:
            print(f"   - {trigger_name} on {table_name}")
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ Triggers setup completed!")
        return True
            
    except Exception as e:
        print(f"❌ Error adding triggers: {str(e)}")
        return False

if __name__ == "__main__":
    add_triggers()
