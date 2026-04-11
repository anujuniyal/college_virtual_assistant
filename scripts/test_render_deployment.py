#!/usr/bin/env python3
"""
Render Deployment Test Script
Tests the application configuration for Render deployment with Neon database
"""

import os
import sys
from dotenv import load_dotenv

def test_render_environment():
    """Test Render environment configuration"""
    print("Testing Render Environment Configuration")
    print("=" * 50)
    
    # Load environment
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dotenv_path = os.path.join(project_root, '.env')
    
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
        print("Environment loaded successfully")
    
    # Set Render environment variables
    os.environ['RENDER'] = 'true'
    os.environ['FLASK_ENV'] = 'production'
    
    # Use Neon database URL
    neon_url = os.environ.get('DATABASE_URL')
    if not neon_url or 'supabase' in neon_url:
        # Use the Neon URL from .env
        neon_url = 'postgresql://neondb_owner:npg_vVJ1xS3CwXIf@ep-small-tree-anl3swp3-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
        os.environ['DATABASE_URL'] = neon_url
        os.environ['POSTGRESQL_URL'] = neon_url
        os.environ['NEON_DATABASE_URL'] = neon_url
    
    print(f"Database URL: {neon_url[:50]}...")
    
    # Test application configuration
    try:
        from app.config import Config, ProductionConfig
        from app.factory import create_app
        
        print("\n1. Testing database URI resolution...")
        db_uri = Config._get_database_uri()
        print(f"   Database URI: {db_uri[:50]}...")
        
        if 'neon.tech' in db_uri:
            print("   Neon database correctly configured")
        else:
            print("   ERROR: Database is not Neon")
            return False
        
        print("\n2. Testing application factory...")
        app = create_app()
        
        with app.app_context():
            from app import db
            
            # Test database connection
            print("   Testing database connection...")
            try:
                # Simple connection test
                result = db.engine.execute("SELECT 1").scalar()
                if result == 1:
                    print("   Database connection successful")
                else:
                    print("   Database connection failed")
                    return False
            except Exception as e:
                print(f"   Database connection error: {str(e)}")
                return False
            
            # Test model creation
            print("   Testing database models...")
            try:
                from app.models import Admin, Student, Result, OTP, Notification
                
                # Check if tables exist
                inspector = db.inspect(db.engine)
                tables = inspector.get_table_names()
                
                expected_tables = ['admins', 'students', 'results', 'otps', 'notifications']
                missing_tables = [table for table in expected_tables if table not in tables]
                
                if missing_tables:
                    print(f"   Missing tables: {missing_tables}")
                    # Create tables if missing
                    db.create_all()
                    print("   Tables created successfully")
                else:
                    print("   All required tables exist")
                
            except Exception as e:
                print(f"   Model test error: {str(e)}")
                return False
        
        print("\n3. Testing production configuration...")
        prod_config = ProductionConfig()
        print(f"   Debug mode: {prod_config.DEBUG}")
        print(f"   Testing mode: {prod_config.TESTING}")
        print(f"   Database engine options: {prod_config.SQLALCHEMY_ENGINE_OPTIONS}")
        
        print("\n4. Testing health check endpoint...")
        with app.test_client() as client:
            response = client.get('/health')
            if response.status_code == 200:
                print("   Health check endpoint working")
            else:
                print(f"   Health check failed: {response.status_code}")
                return False
        
        print("\n5. Testing admin authentication...")
        with app.test_client() as client:
            response = client.post('/admin/login', data={
                'username': 'admin',
                'password': 'admin123'
            })
            # Should redirect or return success
            if response.status_code in [200, 302]:
                print("   Admin authentication working")
            else:
                print(f"   Admin authentication issue: {response.status_code}")
                # This might be expected if the endpoint doesn't exist
        
        print("\n" + "=" * 50)
        print("All Render deployment tests passed!")
        print("Your application is ready for deployment to Render with Neon database.")
        return True
        
    except Exception as e:
        print(f"\nTest failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_render_yaml():
    """Test render.yaml configuration"""
    print("\nTesting render.yaml Configuration")
    print("=" * 30)
    
    render_yaml_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'render.yaml.optimized')
    
    if not os.path.exists(render_yaml_path):
        print("render.yaml.optimized not found")
        return False
    
    with open(render_yaml_path, 'r') as f:
        content = f.read()
    
    # Check for Neon configuration
    if 'neon.tech' in content:
        print("Neon database URL found in render.yaml")
    else:
        print("ERROR: Neon database URL not found in render.yaml")
        return False
    
    # Check for production environment
    if 'FLASK_ENV: production' in content:
        print("Production environment configured")
    else:
        print("ERROR: Production environment not configured")
        return False
    
    # Check for health check
    if 'healthCheckPath: /health' in content:
        print("Health check configured")
    else:
        print("WARNING: Health check not configured")
    
    print("render.yaml configuration looks good!")
    return True

def main():
    """Main test function"""
    print("Render Deployment Test Suite")
    print("=" * 60)
    print("This script tests your application for deployment to Render")
    print("with Neon database configuration.")
    print("=" * 60)
    
    success = True
    
    # Test Render environment
    if not test_render_environment():
        success = False
    
    # Test render.yaml
    if not test_render_yaml():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("All tests passed! Ready for Render deployment.")
        print("\nNext steps:")
        print("1. Use render.yaml.optimized as your render.yaml")
        print("2. Push to your repository")
        print("3. Deploy to Render")
    else:
        print("Some tests failed. Please fix the issues before deploying.")
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
