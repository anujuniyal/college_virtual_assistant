#!/usr/bin/env python3
"""
Test Dashboard Theme and Functionality
"""
import sys
import os

# Add app directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from flask import render_template_string, render_template

def test_theme_consistency():
    """Test theme consistency between base and accounts dashboard"""
    print("=== TESTING DASHBOARD THEME CONSISTENCY ===")
    
    app = create_app()
    
    with app.app_context():
        with app.test_request_context('/accounts/dashboard'):
            # Test 1: Load base dashboard template
            print("\n1. Testing Base Dashboard Template...")
            try:
                base_content = render_template_string('''
                    {% extends "base_dashboard.html" %}
                    {% block title %}Test{% endblock %}
                    {% block sidebar_nav %}
                    <div class="nav-item">
                        <a href="#" class="nav-link active">
                            <i class="bi bi-house"></i>
                            <span>Test</span>
                        </a>
                    </div>
                    {% endblock %}
                    {% block content %}
                    <div class="dashboard-container">
                        <div class="summary-card">
                            <div class="card-icon">🏠</div>
                            <div class="card-title">Test</div>
                            <div class="card-count">100</div>
                        </div>
                    </div>
                    {% endblock %}
                ''')
                print("   Base template: SUCCESS")
                
                # Check for theme elements
                theme_elements = {
                    'sidebar-bg': '--sidebar-bg: #4a148c' in base_content,
                    'primary-color': '--primary-color: #6a1b9a' in base_content,
                    'bootstrap-css': 'bootstrap@5.3.0' in base_content,
                    'dashboard-css': 'dashboard.css' in base_content,
                    'font-awesome': 'font-awesome' in base_content
                }
                
                for element, found in theme_elements.items():
                    status = "✓" if found else "✗"
                    print(f"   {element}: {status}")
                    
            except Exception as e:
                print(f"   Base template error: {e}")
            
            # Test 2: Load accounts dashboard template
            print("\n2. Testing Accounts Dashboard Template...")
            try:
                accounts_content = render_template('accounts_dashboard.html',
                                                 total_students=150,
                                                 total_fee_records=75,
                                                 total_pending=25,
                                                 pending_amount=125000,
                                                 collection_rate=83.3)
                print("   Accounts template: SUCCESS")
                
                # Check for accounts-specific elements
                accounts_elements = {
                    'extends-base': '{% extends "base_dashboard.html" %}' in open('app/templates/accounts_dashboard.html').read(),
                    'accounts-navigation': 'Students' in accounts_content,
                    'fee-cards': 'Total Students' in accounts_content,
                    'quick-actions': 'Quick Actions' in accounts_content,
                    'collection-summary': 'Collection Summary' in accounts_content,
                    'system-status': 'System Status' in accounts_content
                }
                
                for element, found in accounts_elements.items():
                    status = "✓" if found else "✗"
                    print(f"   {element}: {status}")
                    
            except Exception as e:
                print(f"   Accounts template error: {e}")
            
            # Test 3: CSS consistency check
            print("\n3. Testing CSS Consistency...")
            try:
                with open('app/static/css/dashboard.css', 'r') as f:
                    css_content = f.read()
                
                css_checks = {
                    'color-variables': ':root' in css_content and '--sidebar-bg' in css_content,
                    'bootstrap-grid': 'grid-template-columns' in css_content,
                    'animations': '@keyframes' in css_content,
                    'responsive': '@media' in css_content,
                    'hover-effects': ':hover' in css_content,
                    'sidebar-styles': '.sidebar' in css_content
                }
                
                for check, found in css_checks.items():
                    status = "✓" if found else "✗"
                    print(f"   {check}: {status}")
                    
            except Exception as e:
                print(f"   CSS check error: {e}")
            
            # Test 4: JavaScript functionality
            print("\n4. Testing JavaScript Functionality...")
            try:
                with open('app/static/js/dashboard.js', 'r') as f:
                    js_content = f.read()
                
                js_checks = {
                    'dashboard-manager': 'DashboardManager' in js_content,
                    'event-listeners': 'addEventListener' in js_content,
                    'auto-refresh': 'refreshDashboard' in js_content,
                    'mobile-support': 'mobile' in js_content.lower(),
                    'sidebar-toggle': 'toggleSidebar' in js_content,
                    'notifications': 'showNotification' in js_content
                }
                
                for check, found in js_checks.items():
                    status = "✓" if found else "✗"
                    print(f"   {check}: {status}")
                    
            except Exception as e:
                print(f"   JavaScript check error: {e}")
            
            # Test 5: Route accessibility
            print("\n5. Testing Route Accessibility...")
            try:
                client = app.test_client()
                
                # Test dashboard route (should redirect to login)
                response = client.get('/accounts/dashboard', follow_redirects=False)
                print(f"   Dashboard route: {response.status_code} (expected 302 redirect)")
                
                # Test static files
                css_response = client.get('/static/css/dashboard.css')
                js_response = client.get('/static/js/dashboard.js')
                
                print(f"   CSS file: {css_response.status_code} (expected 200)")
                print(f"   JS file: {js_response.status_code} (expected 200)")
                
            except Exception as e:
                print(f"   Route test error: {e}")
        
        print("\n=== DASHBOARD THEME TEST COMPLETED ===")

if __name__ == "__main__":
    test_theme_consistency()
