#!/usr/bin/env python3
"""
Test Analytics Dashboard Theme Consistency
"""
import sys
import os

# Add app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app import create_app
from app.models import Admin
from flask_login import login_user

def test_analytics_theme():
    """Test analytics dashboard theme consistency"""
    print("=== TESTING ANALYTICS DASHBOARD THEME ===")
    
    app = create_app()
    
    with app.app_context():
        admin = Admin.query.filter_by(role='admin').first()
        with app.test_client() as client:
            # Login admin user
            with app.test_request_context():
                login_user(admin)
            
            # Get analytics page
            response = client.get('/admin/analytics', follow_redirects=False)
            print(f'Status: {response.status_code}')
            
            if response.status_code == 200:
                content = response.get_data(as_text=True)
                
                # Check for theme elements
                theme_checks = [
                    ('base_dashboard.html extended', 'extends "base_dashboard.html"' in content or 'extends base_dashboard.html' in content),
                    ('Bootstrap CSS', 'bootstrap' in content.lower()),
                    ('Purple gradient theme', 'sidebar-bg' in content.lower() or '#4a148c' in content.lower()),
                    ('Summary cards', 'summary-cards' in content.lower()),
                    ('Dashboard section', 'dashboard-section' in content.lower()),
                    ('Analytics data displayed', 'Total Queries' in content),
                    ('Weekly report section', 'Weekly Report Information' in content),
                    ('Send report button', 'Send Weekly Report Now' in content),
                    ('JavaScript functionality', 'sendWeeklyReport' in content),
                ]
                
                print('Theme consistency checks:')
                all_passed = True
                for check_name, found in theme_checks:
                    status = '✓' if found else '✗'
                    if not found:
                        all_passed = False
                    print(f'  {status} {check_name}: {found}')
                
                if all_passed:
                    print('\n✅ All theme consistency checks passed!')
                    print('✅ Analytics dashboard now matches base template theme')
                    print('✅ Purple gradient theme applied correctly')
                    print('✅ Bootstrap components integrated')
                    print('✅ Navigation and layout consistent')
                else:
                    print('\n⚠️  Some theme checks failed')
                
                return all_passed
            else:
                print(f'❌ Failed to load analytics page: {response.status_code}')
                return False

if __name__ == "__main__":
    test_analytics_theme()
