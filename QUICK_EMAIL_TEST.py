#!/usr/bin/env python3
"""
Quick Email Test
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app
from app.services.email_service import EmailService

def test_email():
    """Test email with new configuration"""
    print("Testing email configuration...")
    
    app = create_app()
    
    with app.app_context():
        try:
            success = EmailService.send_email(
                to="uniyalanuj1@gmail.com",
                subject="Email Test - EduBot",
                body="This is a test email to verify email configuration is working."
            )
            print(f"Email test result: {'SUCCESS' if success else 'FAILED'}")
            return success
        except Exception as e:
            print(f"Email test error: {e}")
            return False

if __name__ == "__main__":
    test_email()
