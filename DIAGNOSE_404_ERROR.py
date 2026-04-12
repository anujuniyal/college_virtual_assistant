#!/usr/bin/env python3
"""
Diagnose Page Not Found (404) Error
"""
import sys
import os

# Add app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app

def diagnose_routes():
    """Diagnose application routes and endpoints"""
    print("=== DIAGNOSING PAGE NOT FOUND ERROR ===")
    
    app = create_app()
    
    with app.app_context():
        print("\n1. Checking Application Routes...")
        
        # List all routes
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                'rule': rule.rule,
                'endpoint': rule.endpoint,
                'methods': list(rule.methods)
            })
        
        # Sort routes by rule
        routes.sort(key=lambda x: x['rule'])
        
        print(f"   Total routes found: {len(routes)}")
        
        # Check for critical routes
        critical_routes = [
            '/',
            '/health',
            '/login',
            '/admin/dashboard',
            '/accounts/dashboard',
            '/faculty/dashboard'
        ]
        
        print(f"\n2. Checking Critical Routes:")
        for route in critical_routes:
            found = any(r['rule'] == route for r in routes)
            print(f"   {'/' + route if not route.startswith('/') else route}: {'EXISTS' if found else 'MISSING'}")
        
        # Check health check specifically
        health_routes = [r for r in routes if 'health' in r['rule']]
        print(f"\n3. Health Check Routes:")
        for route in health_routes:
            print(f"   {route['rule']} -> {route['endpoint']} ({route['methods']})")
        
        # Check for any potential issues
        print(f"\n4. Potential Issues:")
        
        # Check for duplicate routes
        rule_counts = {}
        for route in routes:
            rule_key = route['rule']
            rule_counts[rule_key] = rule_counts.get(rule_key, 0) + 1
        
        duplicates = {k: v for k, v in rule_counts.items() if v > 1}
        if duplicates:
            print("   Duplicate routes found:")
            for rule, count in duplicates.items():
                print(f"     {rule}: {count} times")
        else:
            print("   No duplicate routes found")
        
        # Check for missing root route
        root_routes = [r for r in routes if r['rule'] == '/']
        if not root_routes:
            print("   WARNING: No root route (/) found")
        else:
            print(f"   Root route: {root_routes[0]['endpoint']}")
        
        return routes

def test_health_endpoint():
    """Test health endpoint directly"""
    print(f"\n5. Testing Health Endpoint...")
    
    app = create_app()
    
    with app.test_client() as client:
        try:
            response = client.get('/health')
            print(f"   Health endpoint status: {response.status_code}")
            if response.status_code == 200:
                print(f"   Health response: {response.get_json()}")
            else:
                print(f"   Health response: {response.data.decode()}")
        except Exception as e:
            print(f"   Health endpoint error: {e}")

def test_root_endpoint():
    """Test root endpoint"""
    print(f"\n6. Testing Root Endpoint...")
    
    app = create_app()
    
    with app.test_client() as client:
        try:
            response = client.get('/')
            print(f"   Root endpoint status: {response.status_code}")
            if response.status_code == 302:
                print(f"   Root redirects to: {response.location}")
            elif response.status_code == 200:
                print(f"   Root endpoint working")
            else:
                print(f"   Root response: {response.data.decode()[:200]}...")
        except Exception as e:
            print(f"   Root endpoint error: {e}")

def check_app_configuration():
    """Check application configuration"""
    print(f"\n7. Checking Application Configuration...")
    
    app = create_app()
    
    with app.app_context():
        print(f"   Server name: {app.config.get('SERVER_NAME', 'Not set')}")
        print(f"   Application root: {app.config.get('APPLICATION_ROOT', 'Not set')}")
        print(f"   URL scheme: {app.config.get('PREFERRED_URL_SCHEME', 'Not set')}")
        print(f"   Debug mode: {app.config.get('DEBUG', 'Not set')}")
        print(f"   Testing mode: {app.config.get('TESTING', 'Not set')}")

def main():
    """Main diagnostic function"""
    print("PAGE NOT FOUND ERROR DIAGNOSTICS")
    print("=" * 50)
    
    try:
        # Diagnose routes
        routes = diagnose_routes()
        
        # Test endpoints
        test_health_endpoint()
        test_root_endpoint()
        
        # Check configuration
        check_app_configuration()
        
        print(f"\n" + "=" * 50)
        print("DIAGNOSIS COMPLETE")
        
        print(f"\nCOMMON 404 ISSUES AND FIXES:")
        print(f"1. Missing root route (/) - Add default route")
        print(f"2. Incorrect URL configuration - Check SERVER_NAME")
        print(f"3. Application not properly started - Check WSGI config")
        print(f"4. Database connection issues - Check database URL")
        print(f"5. Blueprint registration issues - Check blueprint imports")
        
        print(f"\nNEXT STEPS:")
        print(f"1. Check if application is running on Render")
        print(f"2. Verify Render logs for startup errors")
        print(f"3. Test health endpoint: https://your-app.onrender.com/health")
        print(f"4. Check if all blueprints are properly registered")
        
    except Exception as e:
        print(f"Diagnostic error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
