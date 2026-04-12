#!/usr/bin/env python3
"""
Ultimate Email Fix - Try Multiple Solutions
"""
import sys
import os

# Add app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def create_alternative_env():
    """Create alternative .env with different email configurations"""
    print("=== CREATING ALTERNATIVE EMAIL CONFIGURATIONS ===")
    
    # Option 1: Outlook/Hotmail
    outlook_config = """# Email Configuration - Outlook Alternative
MAIL_SERVER=smtp-mail.outlook.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@outlook.com
MAIL_PASSWORD=your-outlook-password
MAIL_DEFAULT_SENDER=your-email@outlook.com
ADMIN_EMAIL=uniyalanuj1@gmail.com

# Keep other configurations
"""
    
    # Option 2: SendGrid (Recommended for Production)
    sendgrid_config = """# Email Configuration - SendGrid Alternative
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=apikey
MAIL_PASSWORD=YOUR_SENDGRID_API_KEY
MAIL_DEFAULT_SENDER=noreply@edubot.management
ADMIN_EMAIL=uniyalanuj1@gmail.com

# Keep other configurations
"""
    
    # Option 3: Gmail with different format
    gmail_fixed_config = """# Email Configuration - Gmail Fixed Format
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=anujjaj007@gmail.com
MAIL_PASSWORD=your-app-password-without-spaces
MAIL_DEFAULT_SENDER=anujjaj007@gmail.com
ADMIN_EMAIL=uniyalanuj1@gmail.com

# Keep other configurations
"""
    
    print("\n1. Outlook/Hotmail Configuration:")
    print("   File: .env.outlook")
    print("   Update: Replace current config with Outlook settings")
    
    print("\n2. SendGrid Configuration:")
    print("   File: .env.sendgrid")
    print("   Update: Replace current config with SendGrid settings")
    
    print("\n3. Gmail Fixed Format:")
    print("   File: .env.gmail-fixed")
    print("   Update: Try without spaces in app password")
    
    # Write alternative configurations
    with open('.env.outlook', 'w') as f:
        f.write(outlook_config)
    print("   ✅ Created .env.outlook")
    
    with open('.env.sendgrid', 'w') as f:
        f.write(sendgrid_config)
    print("   ✅ Created .env.sendgrid")
    
    with open('.env.gmail-fixed', 'w') as f:
        f.write(gmail_fixed_config)
    print("   ✅ Created .env.gmail-fixed")
    
    return True

def test_gmail_password_formats():
    """Test different Gmail password formats"""
    print("\n=== TESTING DIFFERENT GMAIL PASSWORD FORMATS ===")
    
    from app import create_app
    from app.services.email_service import EmailService
    from app.config import Config
    
    app = create_app()
    
    # Test formats to try
    test_formats = [
        "rcazqavcugddl wzt",      # Current (with spaces)
        "rcazqavcugddl wzt",       # Without spaces
        "rcaz qavc ugdd lwzt",      # Different spacing
        "rcazqavcugddl wzt ",     # With trailing space
    ]
    
    for i, test_password in enumerate(test_formats, 1):
        print(f"\n{i}. Testing format: '{test_password}'")
        
        # Temporarily update config
        original_password = Config.MAIL_PASSWORD
        Config.MAIL_PASSWORD = test_password
        
        with app.app_context():
            try:
                success = EmailService.send_email(
                    to="uniyalanuj1@gmail.com",
                    subject=f"Gmail Test {i} - EduBot",
                    body=f"Testing Gmail password format: {test_password}"
                )
                print(f"   Result: {'SUCCESS' if success else 'FAILED'}")
                
                if success:
                    print(f"   ✅ WORKING FORMAT: '{test_password}'")
                    print("   ✅ Update .env with this format!")
                    return test_password
                    
            except Exception as e:
                print(f"   Error: {e}")
            finally:
                # Restore original password
                Config.MAIL_PASSWORD = original_password
    
    print("\n❌ No Gmail format worked. Try alternative email services.")
    return None

def main():
    """Main function to provide comprehensive email fix"""
    print("ULTIMATE EMAIL FIX")
    print("=" * 50)
    
    print("\nPROBLEM: Gmail App Password authentication failing")
    print("ERROR: 535-5.7.8 Username and Password not accepted")
    print("AFFECTED: Forgot password OTP, Faculty credentials emails")
    
    # Step 1: Create alternative configurations
    if create_alternative_env():
        print("\n✅ Alternative configurations created")
    else:
        print("\n❌ Failed to create alternatives")
        return False
    
    # Step 2: Test different Gmail formats
    working_format = test_gmail_password_formats()
    
    if working_format:
        print(f"\n🎉 SOLUTION FOUND!")
        print(f"Working Gmail format: '{working_format}'")
        print("Update your .env file with this format and test again.")
    else:
        print("\n🔄 ALTERNATIVE SOLUTIONS:")
        print("\n1. Use Outlook/Hotmail:")
        print("   - Copy .env.outlook to .env")
        print("   - Update with your Outlook credentials")
        
        print("\n2. Use SendGrid (Production Recommended):")
        print("   - Copy .env.sendgrid to .env")
        print("   - Get SendGrid API key")
        print("   - Update with API configuration")
        
        print("\n3. Try Different Gmail Account:")
        print("   - Create new Gmail account")
        print("   - Generate fresh app password")
        print("   - Update .env with new credentials")
    
    print("\n" + "=" * 50)
    print("NEXT STEPS:")
    print("1. Choose one of the solutions above")
    print("2. Update your .env file accordingly")
    print("3. Test with: python QUICK_EMAIL_TEST.py")
    print("4. Deploy to Render if working")
    
    return working_format is not None

if __name__ == "__main__":
    main()
