#!/usr/bin/env python3
"""
Simple Deployment Test for Supabase Integration
Tests configuration without requiring actual database connection
"""

import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def test_configuration_logic():
    """Test configuration switching logic without database connection"""
    
    print("🔍 Testing Configuration Logic")
    print("=" * 50)
    
    # Test 1: Production with DATABASE_URL
    print("\n1. Production Environment (Render + Supabase)")
    os.environ['FLASK_ENV'] = 'production'
    os.environ['DATABASE_URL'] = 'postgresql://postgres:anujajuniyal007@db.sqzpzxcmhgkbvjfuxgsk.supabase.co:5432/postgres'
    
    try:
        from app.config import Config
        
        database_uri = Config._get_database_uri()
        
        if 'supabase.co' in database_uri and 'postgresql://' in database_uri:
            print("✅ Production: Correctly configured for Supabase")
            print(f"   URI: {database_uri[:60]}...")
        else:
            print("❌ Production: Configuration failed")
            return False
            
    except Exception as e:
        print(f"❌ Production test failed: {str(e)}")
        return False
    
    # Test 2: Development without DATABASE_URL
    print("\n2. Development Environment (Local + SQLite)")
    os.environ['FLASK_ENV'] = 'development'
    if 'DATABASE_URL' in os.environ:
        del os.environ['DATABASE_URL']
    
    try:
        database_uri = Config._get_database_uri()
        
        if 'sqlite' in database_uri:
            print("✅ Development: Correctly configured for SQLite")
            print(f"   URI: {database_uri}")
        else:
            print("❌ Development: Configuration failed")
            return False
            
    except Exception as e:
        print(f"❌ Development test failed: {str(e)}")
        return False
    
    # Test 3: Production engine options
    print("\n3. Production Engine Configuration")
    os.environ['FLASK_ENV'] = 'production'
    os.environ['DATABASE_URL'] = 'postgresql://postgres:anujajuniyal007@db.sqzpzxcmhgkbvjfuxgsk.supabase.co:5432/postgres'
    
    try:
        from app.config import ProductionConfig
        
        engine_options = ProductionConfig.SQLALCHEMY_ENGINE_OPTIONS
        
        required_options = ['pool_size', 'max_overflow', 'pool_timeout', 'pool_recycle']
        
        for option in required_options:
            if option in engine_options:
                print(f"✅ Found engine option: {option}={engine_options[option]}")
            else:
                print(f"❌ Missing engine option: {option}")
                return False
        
        print("✅ Production engine configuration verified")
        
    except Exception as e:
        print(f"❌ Engine configuration test failed: {str(e)}")
        return False
    
    return True

def test_render_yaml():
    """Test render.yaml configuration"""
    
    print("\n🚀 Testing Render Configuration")
    print("=" * 50)
    
    render_yaml_path = os.path.join(project_root, 'render.yaml')
    
    if not os.path.exists(render_yaml_path):
        print("❌ render.yaml not found")
        return False
    
    try:
        with open(render_yaml_path, 'r') as f:
            content = f.read()
        
        # Check for Supabase URL
        if 'db.sqzpzxcmhgkbvjfuxgsk.supabase.co' in content:
            print("✅ Supabase URL configured")
        else:
            print("❌ Supabase URL not found")
            return False
        
        # Check for production environment
        if 'FLASK_ENV' in content and 'production' in content:
            print("✅ Production environment set")
        else:
            print("❌ Production environment not set")
            return False
        
        # Check for simplified gunicorn start command
        if 'gunicorn --bind 0.0.0.0:$PORT' in content:
            print("✅ Simplified start command configured")
        else:
            print("❌ Simplified start command not found")
            return False
        
        print("✅ Render configuration verified")
        return True
        
    except Exception as e:
        print(f"❌ Render configuration test failed: {str(e)}")
        return False

def main():
    """Main test function"""
    
    print("🔍 Simple Deployment Test")
    print("=" * 60)
    print("This test verifies Supabase deployment configuration")
    print("without requiring network connectivity.")
    print("=" * 60)
    
    tests = [
        ("Configuration Logic", test_configuration_logic),
        ("Render Configuration", test_render_yaml)
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
    print("TEST SUMMARY")
    print('='*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All configuration tests passed!")
        print("📱 Your application is ready for deployment to Render.")
        print("🔗 It will automatically:")
        print("   • Switch to Supabase database in production")
        print("   • Use SQLite for local development")
        print("   • Apply proper connection pooling")
        print("   • Support real-time updates")
        return True
    else:
        print("\n⚠️  Some tests failed. Please check the configuration.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
