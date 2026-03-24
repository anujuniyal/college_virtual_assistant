#!/usr/bin/env python3
"""
Deployment Verification Script for Supabase Integration
This script verifies that the application will automatically switch to Supabase when deployed on Render
"""

import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def test_database_switching():
    """Test automatic database switching logic"""
    
    print("🔍 Testing Database Switching Logic")
    print("=" * 50)
    
    # Test 1: Production environment with DATABASE_URL (Render deployment)
    print("\n1. Testing Production Environment (Render + Supabase)")
    os.environ['FLASK_ENV'] = 'production'
    os.environ['DATABASE_URL'] = 'postgresql://postgres:anujajuniyal007@db.sqzpzxcmhgkbvjfuxgsk.supabase.co:5432/postgres'
    
    try:
        # Import after setting environment
        from app.config import Config
        
        database_uri = Config._get_database_uri()
        
        if 'supabase.co' in database_uri and 'postgresql://' in database_uri:
            print("✅ Production: Correctly switches to Supabase")
            print(f"   URI: {database_uri[:60]}...")
        else:
            print("❌ Production: Failed to switch to Supabase")
            print(f"   URI: {database_uri}")
            return False
            
    except Exception as e:
        print(f"❌ Production test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: Development environment (no DATABASE_URL)
    print("\n2. Testing Development Environment (Local + SQLite)")
    os.environ['FLASK_ENV'] = 'development'
    if 'DATABASE_URL' in os.environ:
        del os.environ['DATABASE_URL']
    
    try:
        database_uri = Config._get_database_uri()
        
        if 'sqlite' in database_uri:
            print("✅ Development: Correctly uses SQLite")
            print(f"   URI: {database_uri}")
        else:
            print("❌ Development: Failed to use SQLite")
            print(f"   URI: {database_uri}")
            return False
            
    except Exception as e:
        print(f"❌ Development test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Production without DATABASE_URL (should fail)
    print("\n3. Testing Production Error Handling")
    os.environ['FLASK_ENV'] = 'production'
    # Don't set DATABASE_URL
    
    try:
        database_uri = Config._get_database_uri()
        print("❌ Production should have failed without DATABASE_URL")
        return False
        
    except ValueError as e:
        print("✅ Production: Correctly fails without DATABASE_URL")
        print(f"   Error: {str(e)}")
        
    except Exception as e:
        print(f"❌ Production error handling failed: {str(e)}")
        return False
    
    return True

def test_supabase_connection():
    """Test actual Supabase connection"""
    
    print("\n🔗 Testing Supabase Connection")
    print("=" * 50)
    
    # Set production environment
    os.environ['FLASK_ENV'] = 'production'
    os.environ['DATABASE_URL'] = 'postgresql://postgres:anujajuniyal007@db.sqzpzxcmhgkbvjfuxgsk.supabase.co:5432/postgres'
    
    try:
        from app.factory import create_app
        from app.extensions import db
        from sqlalchemy import text
        
        print("📱 Creating Flask app with production config...")
        app = create_app('production')
        
        with app.app_context():
            print("🔌 Testing database connection...")
            
            # Test basic connection
            result = db.session.execute(text('SELECT version()'))
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL: {version[:50]}...")
            
            # Test table creation/query
            print("📋 Testing database operations...")
            
            # Check if we can create a simple table
            try:
                db.session.execute(text('''
                    CREATE TABLE IF NOT EXISTS deployment_test (
                        id SERIAL PRIMARY KEY,
                        test_timestamp TIMESTAMP DEFAULT NOW()
                    )
                '''))
                
                # Insert test data
                db.session.execute(text('INSERT INTO deployment_test DEFAULT VALUES'))
                db.session.commit()
                
                # Query test data
                result = db.session.execute(text('SELECT COUNT(*) FROM deployment_test'))
                count = result.fetchone()[0]
                
                print(f"✅ Database operations successful: {count} test records")
                
                # Clean up
                db.session.execute(text('DROP TABLE IF EXISTS deployment_test'))
                db.session.commit()
                print("✅ Cleanup completed")
                
            except Exception as e:
                print(f"❌ Database operations failed: {str(e)}")
                return False
            
            print("🎉 Supabase connection test successful!")
            return True
            
    except Exception as e:
        print(f"❌ Supabase connection failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def verify_render_compatibility():
    """Verify Render deployment configuration"""
    
    print("\n🚀 Verifying Render Compatibility")
    print("=" * 50)
    
    # Check if render.yaml exists and has correct configuration
    render_yaml_path = os.path.join(project_root, 'render.yaml')
    
    if not os.path.exists(render_yaml_path):
        print("❌ render.yaml file not found")
        return False
    
    try:
        with open(render_yaml_path, 'r') as f:
            content = f.read()
        
        # Check for required configurations
        required_configs = [
            'DATABASE_URL',
            'FLASK_ENV',
            'postgresql://postgres:anujajuniyal007@db.sqzpzxcmhgkbvjfuxgsk.supabase.co'
        ]
        
        for config in required_configs:
            if config in content:
                print(f"✅ Found: {config}")
            else:
                print(f"❌ Missing: {config}")
                return False
        
        # Check for production FLASK_ENV value
        if 'FLASK_ENV' in content and 'production' in content:
            print("✅ Found: FLASK_ENV=production")
        else:
            print("❌ Missing: FLASK_ENV=production")
            return False
        
        print("✅ Render configuration verified")
        return True
        
    except Exception as e:
        print(f"❌ Failed to verify render.yaml: {str(e)}")
        return False

def main():
    """Main verification function"""
    
    print("🔍 EduBot Deployment Verification")
    print("=" * 60)
    print("This script verifies that your application will automatically")
    print("switch from SQLite to Supabase when deployed on Render.")
    print("=" * 60)
    
    tests = [
        ("Database Switching Logic", test_database_switching),
        ("Supabase Connection", test_supabase_connection),
        ("Render Compatibility", verify_render_compatibility)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print('='*60)
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                print(f"\n✅ {test_name}: PASSED")
            else:
                print(f"\n❌ {test_name}: FAILED")
                
        except Exception as e:
            print(f"\n❌ {test_name}: ERROR - {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("VERIFICATION SUMMARY")
    print('='*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your application is ready for deployment.")
        print("📱 When deployed on Render, it will automatically:")
        print("   • Switch to Supabase database")
        print("   • Use PostgreSQL connection pooling")
        print("   • Store all data in real-time on Supabase")
        return True
    else:
        print("\n⚠️  Some tests failed. Please fix the issues before deploying.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
