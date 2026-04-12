#!/usr/bin/env python3
"""
Gmail App Password Troubleshooting and Alternative Solutions
"""
import sys
import os

# Add app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app
from app.services.email_service import EmailService
from app.config import Config
import smtplib

def test_gmail_auth():
    """Test Gmail authentication with different approaches"""
    print("=== GMAIL AUTHENTICATION TROUBLESHOOTING ===")
    
    app = create_app()
    
    with app.app_context():
        print(f"\nCurrent Configuration:")
        print(f"   Server: {Config.MAIL_SERVER}")
        print(f"   Port: {Config.MAIL_PORT}")
        print(f"   Username: {Config.MAIL_USERNAME}")
        print(f"   Password Length: {len(Config.MAIL_PASSWORD)}")
        print(f"   Password Format: {'Correct' if ' ' in Config.MAIL_PASSWORD else 'No spaces'}")
        
        # Test 1: Direct SMTP connection with debug
        print(f"\n1. Testing Direct SMTP Connection...")
        try:
            server = smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT)
            server.set_debuglevel(1)
            server.starttls()
            
            print(f"   Connected to {Config.MAIL_SERVER}:{Config.MAIL_PORT}")
            print("   TLS encryption started")
            
            # Test authentication
            try:
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                print("   ✅ SMTP Authentication: SUCCESS")
                server.quit()
                return True
            except smtplib.SMTPAuthenticationError as e:
                print(f"   ❌ SMTP Authentication Error: {e}")
                print("   This confirms the app password is invalid")
                server.quit()
                return False
                
        except Exception as e:
            print(f"   ❌ Connection Error: {e}")
            return False
    
    return False

def test_email_service():
    """Test email service directly"""
    print(f"\n2. Testing Email Service...")
    
    app = create_app()
    
    with app.app_context():
        try:
            success = EmailService.send_email(
                to="uniyalanuj1@gmail.com",
                subject="Gmail Test - EduBot",
                body="This is a test email to verify Gmail authentication is working."
            )
            print(f"   Email Service: {'SUCCESS' if success else 'FAILED'}")
            return success
        except Exception as e:
            print(f"   Email Service Error: {e}")
            return False

def suggest_alternatives():
    """Suggest alternative email configurations"""
    print(f"\n3. ALTERNATIVE SOLUTIONS:")
    
    print(f"\n   Option A: Use Outlook/Hotmail")
    print(f"   MAIL_SERVER=smtp-mail.outlook.com")
    print(f"   MAIL_PORT=587")
    print(f"   MAIL_USERNAME=your-email@outlook.com")
    print(f"   MAIL_PASSWORD=your-outlook-password")
    
    print(f"\n   Option B: Use SendGrid (Recommended for Production)")
    print(f"   MAIL_SERVER=smtp.sendgrid.net")
    print(f"   MAIL_PORT=587")
    print(f"   MAIL_USERNAME=apikey")
    print(f"   MAIL_PASSWORD=YOUR_SENDGRID_API_KEY")
    
    print(f"\n   Option C: Use Different Gmail Account")
    print(f"   - Create new Gmail account")
    print(f"   - Generate fresh app password")
    print(f"   - Update .env file")
    
    print(f"\n4. IMMEDIATE FIXES TO TRY:")
    
    print(f"\n   Fix 1: Check App Password Generation")
    print(f"   - Go to: https://myaccount.google.com/apppasswords")
    print(f"   - Make sure 2FA is enabled")
    print(f"   - Select 'Mail' app")
    print(f"   - Use different app name: 'EduBotSystem'")
    print(f"   - Copy password EXACTLY with spaces")
    
    print(f"\n   Fix 2: Check Google Account Security")
    print(f"   - Go to: https://myaccount.google.com/security")
    print(f"   - Check for suspicious activity")
    print(f"   - Make sure account isn't locked")
    
    print(f"\n   Fix 3: Try Different Format")
    print(f"   - Remove spaces from password: rcazqavcugddl wzt")
    print(f"   - Update .env file")

def main():
    """Main troubleshooting function"""
    print("GMAIL AUTHENTICATION TROUBLESHOOTING")
    print("=" * 50)
    
    # Test current configuration
    gmail_works = test_gmail_auth()
    email_service_works = test_email_service()
    
    if gmail_works and email_service_works:
        print(f"\n✅ GMAIL AUTHENTICATION IS WORKING!")
        print(f"   All email features should work correctly")
        return True
    
    print(f"\n❌ GMAIL AUTHENTICATION IS FAILING")
    print(f"   Current app password is not working")
    
    # Provide detailed troubleshooting
    suggest_alternatives()
    
    print(f"\n" + "=" * 50)
    print(f"TROUBLESHOOTING COMPLETE")
    print(f"Follow the suggestions above to fix email issues.")
    
    return False

if __name__ == "__main__":
    main()
