#!/usr/bin/env python3
"""
Test Accounts Dashboard Functionality
"""
import sys
import os

# Add app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app
from app.blueprints.accounts import accounts_bp

def test_accounts_dashboard():
    """Test accounts dashboard functionality"""
    print("=== TESTING ACCOUNTS DASHBOARD FUNCTIONALITY ===")
    
    app = create_app()
    
    with app.app_context():
        # Test 1: Check if routes are properly registered
        print("\n1. Testing Route Registration...")
        try:
            with app.test_request_context('/accounts/dashboard'):
                # Test if dashboard route exists
                for rule in app.url_map.iter_rules():
                    if 'accounts' in rule.rule:
                        print(f"   Route found: {rule.rule} -> {rule.endpoint}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 2: Check template rendering
        print("\n2. Testing Template Rendering...")
        try:
            from flask import render_template
            # Test if accounts dashboard template exists and can render
            template_result = render_template('accounts_dashboard.html',
                                       total_students=100,
                                       total_fee_records=50,
                                       total_pending=10,
                                       pending_amount=50000,
                                       collection_rate=90)
            print("   Template rendering: SUCCESS")
            print(f"   Template length: {len(template_result)} characters")
        except Exception as e:
            print(f"   Template rendering error: {e}")
        
        # Test 3: Check edit profile template
        print("\n3. Testing Edit Profile Template...")
        try:
            edit_profile_result = render_template('edit_profile.html')
            print("   Edit profile template: SUCCESS")
            print(f"   Edit profile template length: {len(edit_profile_result)} characters")
        except Exception as e:
            print(f"   Edit profile template error: {e}")
        
        # Test 4: Check manage notifications template
        print("\n4. Testing Manage Notifications Template...")
        try:
            manage_notifications_result = render_template('manage_notifications.html', notifications=[])
            print("   Manage notifications template: SUCCESS")
            print(f"   Manage notifications template length: {len(manage_notifications_result)} characters")
        except Exception as e:
            print(f"   Manage notifications template error: {e}")
        
        # Test 5: Check blueprint registration
        print("\n5. Testing Blueprint Registration...")
        try:
            if accounts_bp in app.blueprints:
                print("   Accounts blueprint: REGISTERED")
                
                # Check if all routes exist
                routes = []
                for rule in app.url_map.iter_rules():
                    if rule.endpoint and 'accounts' in rule.endpoint:
                        routes.append(rule.rule)
                
                expected_routes = [
                    '/accounts/dashboard',
                    '/accounts/students-fees',
                    '/accounts/edit-profile',
                    '/accounts/manage-notifications',
                    '/accounts/billing'
                ]
                
                for route in expected_routes:
                    if route in routes:
                        print(f"   Route {route}: EXISTS")
                    else:
                        print(f"   Route {route}: MISSING")
            else:
                print("   Accounts blueprint: NOT REGISTERED")
        except Exception as e:
            print(f"   Blueprint registration error: {e}")
        
        print("\n=== ACCOUNTS DASHBOARD TEST COMPLETED ===")
        return True

if __name__ == "__main__":
    test_accounts_dashboard()
