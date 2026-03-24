#!/usr/bin/env python3
"""
Worker debugging script to identify gunicorn worker issues
"""
import os
import sys
import subprocess
import time

def test_worker_startup():
    """Test worker startup locally"""
    print("🧪 Testing worker startup locally...")
    
    try:
        # Test basic app creation
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from app import create_app
        
        print("✅ App import successful")
        
        # Create app multiple times (simulates worker startup)
        for i in range(3):
            print(f"   Creating app instance {i+1}...")
            app = create_app('production')
            
            with app.app_context():
                # Test database connection
                from app.extensions import db
                from sqlalchemy import text
                result = db.session.execute(text('SELECT 1'))
                result.fetchone()
                print(f"   ✅ App {i+1} created and database connected")
        
        print("✅ Worker startup test passed")
        return True
        
    except Exception as e:
        print(f"❌ Worker startup test failed: {str(e)}")
        return False

def test_gunicorn_workers():
    """Test gunicorn with different worker configurations"""
    print("\n🧪 Testing gunicorn worker configurations...")
    
    configs = [
        ("Single Worker", "--workers 1 --threads 1"),
        ("Single Worker + Threads", "--workers 1 --threads 4"),
        ("Multiple Workers", "--workers 2 --threads 1"),
        ("Multiple Workers + Threads", "--workers 2 --threads 2"),
    ]
    
    results = {}
    
    for name, worker_config in configs:
        print(f"\n   Testing: {name}")
        print(f"   Config: {worker_config}")
        
        try:
            cmd = [
                'gunicorn',
                '--bind', '127.0.0.1:5002',
                '--timeout', '10',
                '--max-requests', '10',
                worker_config.split(),
                'wsgi:app'
            ]
            
            # Flatten the command
            cmd = [item for sublist in cmd for item in sublist]
            
            print(f"   Command: {' '.join(cmd)}")
            
            # Start process
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            # Wait for startup
            time.sleep(3)
            
            # Test health endpoint
            try:
                import requests
                response = requests.get('http://127.0.0.1:5002/health', timeout=5)
                if response.status_code == 200:
                    print(f"   ✅ {name} - Health check passed")
                    results[name] = True
                else:
                    print(f"   ❌ {name} - Health check failed: {response.status_code}")
                    results[name] = False
            except Exception as e:
                print(f"   ❌ {name} - Request failed: {str(e)}")
                results[name] = False
            
            # Clean up
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                
        except Exception as e:
            print(f"   ❌ {name} - Failed to start: {str(e)}")
            results[name] = False
    
    return results

def check_worker_memory():
    """Check worker memory usage patterns"""
    print("\n🧪 Checking worker memory patterns...")
    
    try:
        import psutil
        
        # Get current process memory
        process = psutil.Process()
        memory_info = process.memory_info()
        
        print(f"   Current memory usage: {memory_info.rss / 1024 / 1024:.2f} MB")
        print(f"   Available memory: {psutil.virtual_memory().available / 1024 / 1024:.2f} MB")
        
        # Test app creation memory
        initial_memory = memory_info.rss
        
        for i in range(5):
            from app import create_app
            app = create_app('production')
            with app.app_context():
                pass
            del app
        
        final_memory = psutil.Process().memory_info().rss
        memory_increase = (final_memory - initial_memory) / 1024 / 1024
        
        print(f"   Memory increase after 5 app creations: {memory_increase:.2f} MB")
        
        if memory_increase > 50:
            print("   ⚠️  High memory usage detected")
            return False
        else:
            print("   ✅ Memory usage acceptable")
            return True
            
    except Exception as e:
        print(f"   ❌ Memory check failed: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🔧 Worker Debugging Suite")
    print("=" * 50)
    
    tests = [
        ("Worker Startup", test_worker_startup),
        ("Gunicorn Workers", test_gunicorn_workers),
        ("Memory Check", check_worker_memory),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        results[test_name] = test_func()
    
    # Summary
    print(f"\n{'='*20} SUMMARY {'='*20}")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    return all(results.values())

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
