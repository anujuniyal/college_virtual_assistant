#!/usr/bin/env python3
"""
Final System Verification Script
Comprehensive check of all system components before commit
"""

import os
import sys
import sqlite3
import psycopg2
from dotenv import load_dotenv

def check_local_app():
    """Check local application functionality"""
    print("🔍 Checking Local Application")
    print("=" * 40)
    
    try:
        from app.factory import create_app
        app = create_app()
        
        # Test health endpoint
        with app.test_client() as client:
            response = client.get('/health')
            if response.status_code == 200:
                data = response.get_json()
                print(f"✅ Health check: {data.get('status', 'unknown')}")
                print(f"✅ Database: {data.get('database', 'unknown')}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ App factory error: {str(e)}")
        return False

def check_sqlite_data():
    """Check SQLite database"""
    print("\n📊 Checking SQLite Database")
    print("=" * 40)
    
    sqlite_path = 'instance/edubot_management.db'
    
    if not os.path.exists(sqlite_path):
        print("❌ SQLite database not found")
        return False
    
    try:
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        total_records = 0
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            total_records += count
        
        print(f"✅ SQLite: {len(tables)} tables, {total_records} records")
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ SQLite error: {str(e)}")
        return False

def check_supabase_db():
    """Check Supabase database"""
    print("\n🌐 Checking Supabase Database")
    print("=" * 40)
    
    # Load production environment
    load_dotenv('.env.production')
    
    supabase_url = os.environ.get('DATABASE_URL')
    
    if not supabase_url:
        print("❌ DATABASE_URL not found")
        return False
    
    if supabase_url.startswith('postgres://'):
        supabase_url = supabase_url.replace('postgres://', 'postgresql://', 1)
    
    try:
        conn = psycopg2.connect(supabase_url)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        # Check triggers
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.triggers
            WHERE trigger_schema = 'public'
        """)
        trigger_count = cursor.fetchone()[0]
        
        # Check indexes
        cursor.execute("""
            SELECT COUNT(*) FROM pg_indexes
            WHERE schemaname = 'public'
        """)
        index_count = cursor.fetchone()[0]
        
        print(f"✅ Supabase: {len(tables)} tables, {trigger_count} triggers, {index_count} indexes")
        
        # Check for critical tables
        critical_tables = ['admins', 'students', 'faculty', 'notifications', 'chatbot_qa']
        missing_critical = []
        
        for table in critical_tables:
            if table not in tables:
                missing_critical.append(table)
        
        if missing_critical:
            print(f"⚠️  Missing critical tables: {missing_critical}")
            return False
        else:
            print("✅ All critical tables present")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Supabase error: {str(e)}")
        return False

def check_migration_data():
    """Check migration data integrity"""
    print("\n🔄 Checking Migration Data")
    print("=" * 40)
    
    # Load production environment
    load_dotenv('.env.production')
    
    supabase_url = os.environ.get('DATABASE_URL')
    if supabase_url.startswith('postgres://'):
        supabase_url = supabase_url.replace('postgres://', 'postgresql://', 1)
    
    try:
        # Check Supabase data
        pg_conn = psycopg2.connect(supabase_url)
        pg_cursor = pg_conn.cursor()
        
        critical_data = {
            'admins': 0,
            'students': 0,
            'faculty': 0,
            'notifications': 0,
            'chatbot_qa': 0
        }
        
        for table in critical_data:
            pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            critical_data[table] = pg_cursor.fetchone()[0]
        
        total_records = sum(critical_data.values())
        
        print(f"✅ Supabase data: {total_records} total records")
        for table, count in critical_data.items():
            if count > 0:
                print(f"   - {table}: {count} records")
        
        pg_conn.close()
        
        if total_records > 0:
            print("✅ Migration data verified")
            return True
        else:
            print("⚠️  No data found in Supabase")
            return False
            
    except Exception as e:
        print(f"❌ Migration check error: {str(e)}")
        return False

def check_deployment_config():
    """Check deployment configuration"""
    print("\n🚀 Checking Deployment Configuration")
    print("=" * 40)
    
    # Check render.yaml
    if os.path.exists('render.yaml'):
        print("✅ render.yaml exists")
        
        with open('render.yaml', 'r') as f:
            content = f.read()
            
        if 'DATABASE_URL' in content and 'buildCommand' in content:
            print("✅ render.yaml properly configured")
            return True
        else:
            print("❌ render.yaml missing required fields")
            return False
    else:
        print("❌ render.yaml not found")
        return False

def check_environment_files():
    """Check environment files"""
    print("\n🔧 Checking Environment Files")
    print("=" * 40)
    
    files_to_check = ['.env', '.env.production', 'requirements.txt']
    
    all_good = True
    for file in files_to_check:
        if os.path.exists(file):
            print(f"✅ {file} exists")
            
            # Check critical content
            if file == '.env.production':
                with open(file, 'r') as f:
                    content = f.read()
                    if 'DATABASE_URL' in content and 'postgresql://' in content:
                        print(f"   ✅ {file} has Supabase configuration")
                    else:
                        print(f"   ⚠️  {file} may have database issues")
                        all_good = False
        else:
            print(f"❌ {file} missing")
            all_good = False
    
    return all_good

def check_scripts():
    """Check migration and setup scripts"""
    print("\n📜 Checking Scripts")
    print("=" * 40)
    
    script_dir = 'scripts'
    required_scripts = [
        'setup_supabase.py',
        'migrate_to_supabase.py', 
        'deploy_to_render.py',
        'test_deployment.py',
        'fix_missing_tables.py',
        'add_triggers.py'
    ]
    
    all_good = True
    for script in required_scripts:
        script_path = os.path.join(script_dir, script)
        if os.path.exists(script_path):
            print(f"✅ {script}")
        else:
            print(f"❌ {script} missing")
            all_good = False
    
    return all_good

def final_verification():
    """Run final comprehensive verification"""
    print("🔍 FINAL SYSTEM VERIFICATION")
    print("=" * 60)
    print("Checking all components before commit...\n")
    
    checks = [
        ("Local Application", check_local_app),
        ("SQLite Database", check_sqlite_data),
        ("Supabase Database", check_supabase_db),
        ("Migration Data", check_migration_data),
        ("Deployment Config", check_deployment_config),
        ("Environment Files", check_environment_files),
        ("Scripts", check_scripts)
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"❌ {name} check failed: {str(e)}")
            results[name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:<25} {status}")
        if result:
            passed += 1
    
    print("-" * 60)
    print(f"Overall: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 ALL SYSTEMS READY FOR COMMIT!")
        return True
    else:
        print(f"\n⚠️  {total - passed} issues need to be resolved")
        return False

if __name__ == "__main__":
    success = final_verification()
    sys.exit(0 if success else 1)
