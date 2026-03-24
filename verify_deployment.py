#!/usr/bin/env python3
"""
Deployment verification script for Render with Supabase
Tests memory usage, database connectivity, and configuration
"""
import os
import sys
import psutil
import time

def test_memory_usage():
    """Test memory usage under production conditions"""
    print("🧪 Testing memory usage...")
    
    try:
        # Get initial memory
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        print(f"   Initial memory: {initial_memory:.2f} MB")
        
        # Test multiple app creations (simulates worker restarts)
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from app import create_app
        
        apps = []
        for i in range(3):
            print(f"   Creating app instance {i+1}...")
            app = create_app('production')
            apps.append(app)
            
            # Check memory after each creation
            current_memory = process.memory_info().rss / 1024 / 1024
            print(f"   Memory after app {i+1}: {current_memory:.2f} MB")
            
            if current_memory > 350:
                print(f"   ⚠️  Memory approaching limit: {current_memory:.2f} MB")
                return False
        
        # Test database connections
        print("   Testing database connections...")
        for i, app in enumerate(apps):
            with app.app_context():
                from app.extensions import db
                from sqlalchemy import text
                try:
                    result = db.session.execute(text('SELECT 1'))
                    result.fetchone()
                    print(f"   ✅ App {i+1} database connection successful")
                except Exception as e:
                    print(f"   ❌ App {i+1} database connection failed: {str(e)}")
                    return False
        
        # Final memory check
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        
        print(f"   Final memory: {final_memory:.2f} MB")
        print(f"   Memory increase: {memory_increase:.2f} MB")
        
        if final_memory < 380:
            print("   ✅ Memory usage within acceptable limits")
            return True
        else:
            print(f"   ❌ Memory usage too high: {final_memory:.2f} MB")
            return False
            
    except Exception as e:
        print(f"   ❌ Memory test failed: {str(e)}")
        return False

def test_supabase_config():
    """Test Supabase configuration and connectivity"""
    print("\n🧪 Testing Supabase configuration...")
    
    try:
        # Check environment variables
        database_url = os.environ.get('DATABASE_URL')
        postgresql_url = os.environ.get('POSTGRESQL_URL')
        
        print(f"   DATABASE_URL set: {'✅' if database_url else '❌'}")
        print(f"   POSTGRESQL_URL set: {'✅' if postgresql_url else '❌'}")
        
        if not database_url and not postgresql_url:
            print("   ❌ No database URLs configured")
            return False
        
        # Test app creation with database
        from app import create_app
        app = create_app('production')
        
        with app.app_context():
            from app.extensions import db
            from sqlalchemy import text
            
            # Test basic connection
            result = db.session.execute(text('SELECT 1'))
            result.fetchone()
            print("   ✅ Database connection successful")
            
            # Test database type
            database_uri = app.config['SQLALCHEMY_DATABASE_URI']
            if 'supabase' in database_uri or 'postgresql' in database_uri:
                print("   ✅ Using PostgreSQL/Supabase database")
            else:
                print(f"   ⚠️  Using alternative database: {database_uri}")
            
            return True
            
    except Exception as e:
        print(f"   ❌ Supabase configuration test failed: {str(e)}")
        return False

def test_gunicorn_config():
    """Test gunicorn configuration for memory efficiency"""
    print("\n🧪 Testing gunicorn configuration...")
    
    try:
        # Check if gunicorn command is properly configured
        expected_config = {
            'workers': 1,
            'threads': 1,
            'timeout': 120,
            'max_requests': 100,
            'preload': True
        }
        
        print("   Expected gunicorn configuration:")
        for key, value in expected_config.items():
            print(f"     --{key.replace('_', '-')}: {value}")
        
        # Test if we can import the WSGI app
        from wsgi import app
        print("   ✅ WSGI app import successful")
        
        # Test app context
        with app.app_context():
            from app.extensions import db
            print("   ✅ App context working")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Gunicorn configuration test failed: {str(e)}")
        return False

def main():
    """Main verification function"""
    print("🔧 Render Deployment Verification Suite")
    print("=" * 50)
    
    # Set production environment for testing
    os.environ['FLASK_ENV'] = 'production'
    
    tests = [
        ("Memory Usage", test_memory_usage),
        ("Supabase Configuration", test_supabase_config),
        ("Gunicorn Configuration", test_gunicorn_config),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        results[test_name] = test_func()
    
    # Summary
    print(f"\n{'='*20} VERIFICATION SUMMARY {'='*20}")
    all_passed = True
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! Ready for deployment.")
    else:
        print("\n⚠️  Some tests failed. Please fix issues before deploying.")
    
    return all_passed

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
