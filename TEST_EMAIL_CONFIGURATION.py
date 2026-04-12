#!/usr/bin/env python3
"""
Test Email Configuration and SMTP Settings
"""
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app
from app.services.email_service import EmailService
from app.services.otp_service import OTPService
from app.config import Config

def test_email_configuration():
    """Test email configuration and SMTP settings"""
    print("=== TESTING EMAIL CONFIGURATION ===")
    
    app = create_app()
    
    with app.app_context():
        print("\n1. Checking Email Configuration...")
        print(f"   MAIL_SERVER: {Config.MAIL_SERVER}")
        print(f"   MAIL_PORT: {Config.MAIL_PORT}")
        print(f"   MAIL_USERNAME: {Config.MAIL_USERNAME}")
        print(f"   MAIL_PASSWORD: {'*' * len(Config.MAIL_PASSWORD) if Config.MAIL_PASSWORD else 'NOT_SET'}")
        print(f"   MAIL_DEFAULT_SENDER: {Config.MAIL_DEFAULT_SENDER}")
        print(f"   MAIL_USE_TLS: {Config.MAIL_USE_TLS}")
        
        # Check if configuration is complete
        config_complete = all([
            Config.MAIL_SERVER,
            Config.MAIL_USERNAME,
            Config.MAIL_PASSWORD,
            Config.MAIL_DEFAULT_SENDER
        ])
        
        print(f"   Configuration Complete: {config_complete}")
        
        if not config_complete:
            print("   ERROR: Email configuration is incomplete!")
            return False
        
        print("\n2. Testing Basic Email Sending...")
        try:
            test_email = "uniyalanuj1@gmail.com"  # Admin email
            subject = "Email Configuration Test - EduBot"
            body = """
This is a test email to verify that the email configuration is working correctly.

If you receive this email, the email service is functioning properly.

Test Details:
- Timestamp: Just now
- Service: EduBot Email Service
- Purpose: Configuration Test

Best regards,
EduBot System
"""
            
            success = EmailService.send_email(test_email, subject, body)
            print(f"   Basic Email Test: {'SUCCESS' if success else 'FAILED'}")
            
            if not success:
                print("   ERROR: Basic email sending failed!")
                return False
                
        except Exception as e:
            print(f"   ERROR: Exception during basic email test: {e}")
            return False
        
        print("\n3. Testing OTP Service...")
        try:
            test_otp_email = "uniyalanuj1@gmail.com"
            otp_code, otp_success = OTPService.generate_otp(test_otp_email)
            print(f"   OTP Generated: {otp_code}")
            print(f"   OTP Email Test: {'SUCCESS' if otp_success else 'FAILED'}")
            
            if not otp_success:
                print("   ERROR: OTP email sending failed!")
                return False
                
        except Exception as e:
            print(f"   ERROR: Exception during OTP test: {e}")
            return False
        
        print("\n4. Testing Faculty Credentials Email...")
        try:
            faculty_email = "uniyalanuj1@gmail.com"
            faculty_name = "Test Faculty"
            faculty_password = "TestPass123"
            faculty_role = "faculty"
            
            subject = "Your Faculty Login Credentials - College Virtual Assistant"
            body = f"""
Dear {faculty_name},

Your faculty account has been created successfully in the College Virtual Assistant system.

Login Details:
- Email: {faculty_email}
- Password: {faculty_password}
- Role: {faculty_role}

You can now access the faculty dashboard using these credentials.

Important:
- Please change your password after first login
- Keep your credentials secure
- Contact admin if you face any issues

Best regards,
College Administration
"""
            
            success = EmailService.send_email(faculty_email, subject, body)
            print(f"   Faculty Credentials Test: {'SUCCESS' if success else 'FAILED'}")
            
            if not success:
                print("   ERROR: Faculty credentials email failed!")
                return False
                
        except Exception as e:
            print(f"   ERROR: Exception during faculty credentials test: {e}")
            return False
        
        print("\n=== EMAIL CONFIGURATION TEST COMPLETED ===")
        print("All email tests passed successfully!")
        return True

def test_smtp_connection():
    """Test direct SMTP connection"""
    print("\n=== TESTING DIRECT SMTP CONNECTION ===")
    
    try:
        import smtplib
        
        server = smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT)
        server.set_debuglevel(1)
        
        print("   Starting TLS encryption...")
        server.starttls()
        
        print("   Attempting login...")
        server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
        
        print("   SMTP Connection: SUCCESS")
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"   SMTP Authentication Error: {e}")
        print("   SOLUTION: Check Gmail username and app password")
        return False
    except smtplib.SMTPException as e:
        print(f"   SMTP Error: {e}")
        return False
    except Exception as e:
        print(f"   Connection Error: {e}")
        return False

if __name__ == '__main__':
    print("Starting comprehensive email configuration test...")
    
    # Test email configuration
    email_success = test_email_configuration()
    
    # Test SMTP connection
    smtp_success = test_smtp_connection()
    
    if email_success and smtp_success:
        print("\n** ALL EMAIL TESTS PASSED! **")
        print("Email functionality is working correctly.")
    else:
        print("\n** SOME EMAIL TESTS FAILED! **")
        print("Please check the error messages above.")
        print("\nCommon issues:")
        print("1. Gmail App Password not configured")
        print("2. 2-Factor Authentication not enabled")
        print("3. Firewall blocking SMTP connections")
        print("4. Incorrect email configuration")
    
    sys.exit(0 if (email_success and smtp_success) else 1)
