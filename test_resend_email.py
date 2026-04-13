#!/usr/bin/env python3
"""
Test Resend Email Service
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app
from app.services.email_service import EmailService

def test_resend_email():
    """Test Resend email service"""
    print("Testing Resend Email Service...")
    
    app = create_app()
    
    with app.app_context():
        try:
            success = EmailService.send_email(
                to="gojo976038@gmail.com",
                subject="Test OTP - College Virtual Assistant",
                body="This is a test OTP email to verify Resend API is working properly.\n\nYour test OTP is: 123456\n\nIf you receive this email, Resend is working correctly!",
                html="<p>This is a test OTP email to verify Resend API is working properly.</p><p><strong>Your test OTP is: 123456</strong></p><p>If you receive this email, Resend is working correctly!</p>"
            )
            
            if success:
                print("✅ Test email sent successfully via Resend API!")
                print("📧 Check gojo976038@gmail.com for the test email")
            else:
                print("❌ Test email failed")
                
        except Exception as e:
            print(f"❌ Test failed with error: {str(e)}")

if __name__ == "__main__":
    test_resend_email()
