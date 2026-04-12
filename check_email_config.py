#!/usr/bin/env python3
"""
Check Email Configuration - Can be run as a standalone script or imported
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app

def check_email_config():
    """Check email configuration status"""
    app = create_app()
    
    with app.app_context():
        mail_server = app.config.get('MAIL_SERVER')
        mail_username = app.config.get('MAIL_USERNAME')
        mail_password = app.config.get('MAIL_PASSWORD')
        
        print("=== Email Configuration Check ===")
        print(f"MAIL_SERVER: {mail_server}")
        print(f"MAIL_USERNAME: {mail_username}")
        print(f"MAIL_PASSWORD: {'SET' if mail_password else 'NOT_SET'}")
        
        if all([mail_server, mail_username, mail_password]):
            print("Status: COMPLETE")
            return True
        else:
            print("Status: INCOMPLETE")
            return False

if __name__ == "__main__":
    check_email_config()
