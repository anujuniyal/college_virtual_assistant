#!/usr/bin/env python3
"""
Test script to verify deployment fixes before pushing to Render
"""
import os
import sys
import requests
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_local_startup():
    """Test local application startup"""
    print("🧪 Testing local application startup...")
    
    try:
        # Test app creation
        from app import create_app
        
        # Create app with production config
        app = create_app('production')
        
        with app.app_context():
            # Test database connection
            from app.extensions import db
            from sqlalchemy import text
            
            result = db.session.execute(text('SELECT 1 as test'))
            result.fetchone()
            
            print("✅ Local startup successful")
            print(f"✅ Database connected: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
            
            # Test health endpoint
            with app.test_client() as client:
                response = client.get('/health')
                if response.status_code == 200:
                    print("✅ Health endpoint working")
                    print(f"   Response: {response.get_json()}")
                else:
                    print(f"❌ Health endpoint failed: {response.status_code}")
                    
        return True
        
    except Exception as e:
        print(f"❌ Local startup failed: {str(e)}")
        return False

def test_gunicorn_config():
    """Test gunicorn configuration"""
    print("\n🧪 Testing gunicorn configuration...")
    
    try:
        import subprocess
        import signal
        
        # Start gunicorn with the same command as Render
        cmd = [
            'gunicorn', 
            '--bind', '127.0.0.1:5001',  # Different port to avoid conflicts
            '--workers', '2', 
            '--timeout', '30',  # Shorter timeout for testing
            '--preload', 
            'wsgi:app'
        ]
        
        print(f"   Command: {' '.join(cmd)}")
        
        # Start process
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.getcwd()
        )
        
        # Wait a bit for startup
        time.sleep(5)
        
        # Test health endpoint
        try:
            response = requests.get('http://127.0.0.1:5001/health', timeout=10)
            if response.status_code == 200:
                print("✅ Gunicorn health endpoint working")
                print(f"   Response: {response.get_json()}")
            else:
                print(f"❌ Gunicorn health endpoint failed: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Gunicorn request failed: {str(e)}")
        
        # Clean up
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            
        return True
        
    except Exception as e:
        print(f"❌ Gunicorn test failed: {str(e)}")
        return False

def check_render_config():
    """Check render.yaml configuration"""
    print("\n🧪 Checking render.yaml configuration...")
    
    try:
        import yaml
        
        with open('render.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        service = config['services'][0]
        
        # Check for issues
        issues = []
        
        # Check start command
        start_cmd = service.get('startCommand', '')
        if '--preload' not in start_cmd:
            issues.append("Missing --preload flag")
        if '--workers 4' in start_cmd:
            issues.append("Too many workers (should be 2 for free tier)")
        if '--timeout 120' in start_cmd:
            issues.append("Timeout too short (should be 300)")
        
        # Check environment variables
        env_vars = service.get('envVars', [])
        admin_email_count = sum(1 for var in env_vars if var.get('key') == 'DEFAULT_ADMIN_EMAIL')
        admin_pass_count = sum(1 for var in env_vars if var.get('key') == 'DEFAULT_ADMIN_PASSWORD')
        
        if admin_email_count > 1:
            issues.append(f"Duplicate DEFAULT_ADMIN_EMAIL ({admin_email_count} times)")
        if admin_pass_count > 1:
            issues.append(f"Duplicate DEFAULT_ADMIN_PASSWORD ({admin_pass_count} times)")
        
        if issues:
            print("❌ Configuration issues found:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("✅ Configuration looks good")
            
        return len(issues) == 0
        
    except Exception as e:
        print(f"❌ Config check failed: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 Deployment Fix Verification")
    print("=" * 50)
    
    tests = [
        ("Local Startup", test_local_startup),
        ("Gunicorn Config", test_gunicorn_config),
        ("Render Config", check_render_config),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        results[test_name] = test_func()
    
    # Summary
    print(f"\n{'='*20} SUMMARY {'='*20}")
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Ready for deployment.")
        return 0
    else:
        print("⚠️  Some tests failed. Fix issues before deploying.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
