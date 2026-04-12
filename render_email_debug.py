#!/usr/bin/env python3
"""
Render Email Debug - Run this on Render to debug email issues
"""
import os

def debug_render_email():
    """Debug email configuration specifically for Render"""
    print("=== RENDER EMAIL DEBUG ===")
    
    # Check if we're actually on Render
    is_render = (
        os.environ.get('RENDER') == 'true' or 
        os.environ.get('RENDER_SERVICE_ID') is not None or
        os.environ.get('RENDER_SERVICE_NAME') is not None or
        os.path.exists('/etc/render') or
        'render.com' in os.environ.get('HOME', '')
    )
    
    print(f"Running on Render: {is_render}")
    
    # Check email environment variables
    email_config = {
        'MAIL_SERVER': os.environ.get('MAIL_SERVER'),
        'MAIL_PORT': os.environ.get('MAIL_PORT'),
        'MAIL_USE_TLS': os.environ.get('MAIL_USE_TLS'),
        'MAIL_USERNAME': os.environ.get('MAIL_USERNAME'),
        'MAIL_PASSWORD': 'SET' if os.environ.get('MAIL_PASSWORD') else 'NOT_SET',
        'MAIL_DEFAULT_SENDER': os.environ.get('MAIL_DEFAULT_SENDER'),
        'ADMIN_EMAIL': os.environ.get('ADMIN_EMAIL')
    }
    
    print("\nEmail Environment Variables:")
    for key, value in email_config.items():
        print(f"  {key}: {value}")
    
    # Check completeness
    complete = all([
        email_config['MAIL_SERVER'],
        email_config['MAIL_USERNAME'],
        email_config['MAIL_PASSWORD'] != 'NOT_SET'
    ])
    
    print(f"\nEmail Configuration Complete: {complete}")
    
    if not complete:
        print("Missing variables:")
        if not email_config['MAIL_SERVER']:
            print("  - MAIL_SERVER")
        if not email_config['MAIL_USERNAME']:
            print("  - MAIL_USERNAME")
        if email_config['MAIL_PASSWORD'] == 'NOT_SET':
            print("  - MAIL_PASSWORD")

if __name__ == "__main__":
    debug_render_email()
