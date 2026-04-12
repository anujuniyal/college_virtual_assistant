#!/usr/bin/env python3
"""
Test Server Configuration Fix
"""
import sys
import os

# Add app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_server_config():
    """Test server configuration without warnings"""
    print("=== TESTING SERVER CONFIGURATION ===")
    
    from app import create_app
    
    app = create_app()
    
    with app.app_context():
        print(f"Server Name: {app.config.get('SERVER_NAME', 'Not set')}")
        print(f"URL Scheme: {app.config.get('PREFERRED_URL_SCHEME', 'Not set')}")
        print(f"Application Root: {app.config.get('APPLICATION_ROOT', 'Not set')}")
        
        # Test URL generation
        with app.test_request_context():
            login_url = app.url_for('auth.login')
            print(f"Login URL: {login_url}")
            
            admin_url = app.url_for('admin.admin_dashboard_main')
            print(f"Admin URL: {admin_url}")
            
            accounts_url = app.url_for('accounts.accounts_dashboard')
            print(f"Accounts URL: {accounts_url}")
    
    print("\n✅ Server configuration test completed")
    print("No Flask warnings expected")

if __name__ == "__main__":
    test_server_config()
