#!/usr/bin/env python3
"""
Debug Render Email Configuration
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app

def debug_email_config():
    """Debug email configuration in Render environment"""
    print("=== Email Configuration Debug ===")
    
    # Check environment variables
    email_vars = [
        'MAIL_SERVER',
        'MAIL_PORT', 
        'MAIL_USE_TLS',
        'MAIL_USERNAME',
        'MAIL_PASSWORD',
        'MAIL_DEFAULT_SENDER',
        'ADMIN_EMAIL'
    ]
    
    print("\n--- Environment Variables ---")
    for var in email_vars:
        value = os.environ.get(var, 'NOT_SET')
        if var == 'MAIL_PASSWORD' and value != 'NOT_SET':
            # Show only first/last few chars for security
            masked = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
            print(f"{var}: {masked}")
        else:
            print(f"{var}: {value}")
    
    # Check Render detection
    print("\n--- Render Detection ---")
    render_vars = ['RENDER', 'RENDER_SERVICE_ID', 'RENDER_SERVICE_NAME']
    for var in render_vars:
        print(f"{var}: {os.environ.get(var, 'NOT_SET')}")
    
    is_render = (
        os.environ.get('RENDER') == 'true' or 
        os.environ.get('RENDER_SERVICE_ID') is not None or
        os.environ.get('RENDER_SERVICE_NAME') is not None or
        os.path.exists('/etc/render') or
        'render.com' in os.environ.get('HOME', '')
    )
    print(f"Is Render: {is_render}")
    
    # Check Flask app config
    print("\n--- Flask App Config ---")
    app = create_app()
    with app.app_context():
        for var in email_vars:
            value = app.config.get(var, 'NOT_SET')
            if var == 'MAIL_PASSWORD' and value != 'NOT_SET':
                masked = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
                print(f"{var}: {masked}")
            else:
                print(f"{var}: {value}")
    
    # Check if email config is complete
    print("\n--- Email Configuration Status ---")
    with app.app_context():
        mail_server = app.config.get('MAIL_SERVER')
        mail_username = app.config.get('MAIL_USERNAME')
        mail_password = app.config.get('MAIL_PASSWORD')
        
        if all([mail_server, mail_username, mail_password]):
            print("Status: COMPLETE - Email configuration is ready")
        else:
            print("Status: INCOMPLETE - Missing configuration")
            if not mail_server:
                print("  Missing: MAIL_SERVER")
            if not mail_username:
                print("  Missing: MAIL_USERNAME")
            if not mail_password:
                print("  Missing: MAIL_PASSWORD")

if __name__ == "__main__":
    debug_email_config()
