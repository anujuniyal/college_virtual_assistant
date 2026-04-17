#!/usr/bin/env python3
"""
Test Analytics Dashboard Functionality
"""
import sys
import os

# Add app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app import create_app
from app.services.analytics_service import AnalyticsService

def test_analytics_dashboard():
    """Test analytics dashboard functionality"""
    print("=== TESTING ANALYTICS DASHBOARD FUNCTIONALITY ===")
    
    app = create_app()
    
    with app.app_context():
        # Test 1: Check if analytics route is properly registered
        print("\n1. Testing Route Registration...")
        try:
            with app.test_request_context('/admin/analytics'):
                # Test if analytics route exists
                analytics_route_found = False
                for rule in app.url_map.iter_rules():
                    if 'admin.analytics' in rule.endpoint:
                        print(f"   ✓ Route found: {rule.rule} -> {rule.endpoint}")
                        analytics_route_found = True
                        break
                
                if not analytics_route_found:
                    print("   ✗ Analytics route not found!")
                    return False
        except Exception as e:
            print(f"   ✗ Error checking route: {e}")
            return False
        
        # Test 2: Test AnalyticsService functionality
        print("\n2. Testing Analytics Service...")
        try:
            # Test get_analytics method
            analytics_data = AnalyticsService.get_analytics()
            print(f"   ✓ Analytics data retrieved: {analytics_data}")
            
            # Test get_weekly_report_data method
            weekly_data = AnalyticsService.get_weekly_report_data()
            print(f"   ✓ Weekly data retrieved: {weekly_data}")
            
        except Exception as e:
            print(f"   ✗ Error testing analytics service: {e}")
            return False
        
        # Test 3: Test analytics route with mock admin user
        print("\n3. Testing Analytics Route Response...")
        try:
            with app.test_client() as client:
                # Create a test session with admin user
                with client.session_transaction() as sess:
                    # Mock admin user session
                    sess['user_id'] = 1
                    sess['_fresh'] = True
                
                # Test GET request to analytics route
                response = client.get('/admin/analytics', follow_redirects=True)
                
                if response.status_code == 200:
                    print("   ✓ Analytics route returns 200 OK")
                    
                    # Check if response contains expected content
                    response_text = response.get_data(as_text=True)
                    if 'Analytics Dashboard' in response_text:
                        print("   ✓ Response contains Analytics Dashboard title")
                    else:
                        print("   ✗ Response missing Analytics Dashboard title")
                    
                    if 'Total Queries' in response_text:
                        print("   ✓ Response contains Total Queries section")
                    else:
                        print("   ✗ Response missing Total Queries section")
                        
                else:
                    print(f"   ✗ Analytics route returned {response.status_code}")
                    print(f"   Response: {response.get_data(as_text=True)[:200]}...")
                    return False
                    
        except Exception as e:
            print(f"   ✗ Error testing analytics route: {e}")
            return False
        
        # Test 4: Test weekly report send route
        print("\n4. Testing Weekly Report Send Route...")
        try:
            with app.test_client() as client:
                with client.session_transaction() as sess:
                    sess['user_id'] = 1
                    sess['_fresh'] = True
                
                response = client.post('/admin/send-weekly-report', follow_redirects=True)
                
                if response.status_code in [200, 302]:
                    print(f"   ✓ Weekly report route responds: {response.status_code}")
                else:
                    print(f"   ✗ Weekly report route failed: {response.status_code}")
                    
        except Exception as e:
            print(f"   ✗ Error testing weekly report route: {e}")
        
        print("\n=== ANALYTICS DASHBOARD TEST COMPLETE ===")
        return True

if __name__ == "__main__":
    test_analytics_dashboard()
