#!/usr/bin/env python3
"""
Test Gmail Authentication with Detailed Debugging
"""
import sys
import os
import smtplib

# Add app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_gmail_auth_direct():
    """Test Gmail authentication directly with SMTP"""
    print("=== DIRECT GMAIL AUTHENTICATION TEST ===")
    
    # Test with different password formats
    passwords = [
        "rcaz qavc ugdd lwzt",  # With spaces
        "rcazqavcugddl wzt",    # Without spaces
        "rcazqavcugddl wzt",    # Alternative format
    ]
    
    username = "anujjaj007@gmail.com"
    server = "smtp.gmail.com"
    port = 587
    
    for i, password in enumerate(passwords):
        print(f"\nTesting password format {i+1}: {'WITH SPACES' if ' ' in password else 'WITHOUT SPACES'}")
        print(f"Password: {'*' * len(password)}")
        
        try:
            # Create SMTP connection
            smtp = smtplib.SMTP(server, port)
            smtp.set_debuglevel(0)  # Disable debug for cleaner output
            
            # Start TLS
            smtp.starttls()
            
            # Try login
            smtp.login(username, password)
            print(f"SUCCESS: Authentication successful with format {i+1}")
            smtp.quit()
            return True, password
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"FAILED: Authentication error with format {i+1}")
            print(f"Error: {str(e)}")
            smtp.quit()
            
        except Exception as e:
            print(f"ERROR: Unexpected error with format {i+1}: {str(e)}")
            try:
                smtp.quit()
            except:
                pass
    
    return False, None

def test_gmail_auth_with_app():
    """Test Gmail authentication using app configuration"""
    print("\n=== GMAIL AUTHENTICATION WITH APP CONFIG ===")
    
    from app import create_app
    
    app = create_app()
    
    with app.app_context():
        # Get configuration
        mail_server = app.config.get('MAIL_SERVER')
        mail_port = app.config.get('MAIL_PORT')
        mail_username = app.config.get('MAIL_USERNAME')
        mail_password = app.config.get('MAIL_PASSWORD')
        
        print(f"Server: {mail_server}")
        print(f"Port: {mail_port}")
        print(f"Username: {mail_username}")
        print(f"Password: {'SET' if mail_password else 'NOT SET'}")
        
        if not all([mail_server, mail_port, mail_username, mail_password]):
            print("Configuration incomplete")
            return False
        
        try:
            # Test SMTP connection
            smtp = smtplib.SMTP(mail_server, int(mail_port))
            smtp.set_debuglevel(1)  # Enable debug for detailed output
            
            # Start TLS
            smtp.starttls()
            
            # Try login
            smtp.login(mail_username, mail_password)
            print("SUCCESS: Authentication successful with app config")
            smtp.quit()
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"FAILED: Authentication error with app config")
            print(f"Error: {str(e)}")
            smtp.quit()
            return False
            
        except Exception as e:
            print(f"ERROR: Unexpected error with app config: {str(e)}")
            try:
                smtp.quit()
            except:
                pass
            return False

def test_email_service():
    """Test email service directly"""
    print("\n=== EMAIL SERVICE TEST ===")
    
    from app import create_app
    from app.services.email_service import EmailService
    
    app = create_app()
    
    with app.app_context():
        try:
            # Test email sending
            result = EmailService.send_email(
                to="uniyalanuj1@gmail.com",
                subject="Gmail Auth Test - College Virtual Assistant",
                body="This is a test email to verify Gmail authentication.\n\nTest sent at: Just now"
            )
            print(f"Email service result: {'SUCCESS' if result else 'FAILED'}")
            return result
            
        except Exception as e:
            print(f"Email service error: {str(e)}")
            return False

def main():
    """Main test function"""
    print("GMAIL AUTHENTICATION COMPREHENSIVE TEST")
    print("=" * 50)
    
    results = {
        'direct_auth': False,
        'app_config_auth': False,
        'email_service': False,
        'working_password': None
    }
    
    try:
        # Test direct authentication
        success, working_password = test_gmail_auth_direct()
        results['direct_auth'] = success
        results['working_password'] = working_password
        
        # Test with app configuration
        results['app_config_auth'] = test_gmail_auth_with_app()
        
        # Test email service
        results['email_service'] = test_email_service()
        
        print("\n" + "=" * 50)
        print("TEST RESULTS SUMMARY")
        print("=" * 50)
        
        for test, result in results.items():
            if test == 'working_password':
                if result:
                    print(f"Working Password Format: FOUND")
                    print(f"Password: {result}")
                else:
                    print(f"Working Password Format: NOT FOUND")
            else:
                status = "PASS" if result else "FAIL"
                print(f"{test.replace('_', ' ').title()}: {status}")
        
        # Recommendations
        print("\nRECOMMENDATIONS:")
        
        if not results['direct_auth']:
            print("1. Generate a new Gmail App Password")
            print("2. Ensure 2-step verification is enabled")
            print("3. Check Gmail account security settings")
            print("4. Try using a different Gmail account")
        
        if not results['app_config_auth']:
            print("5. Check environment variable loading")
            print("6. Verify render-docker.yaml configuration")
        
        if not results['email_service']:
            print("7. Check EmailService implementation")
            print("8. Verify SMTP configuration")
        
        if results['working_password']:
            print(f"\nWORKING PASSWORD FORMAT: {results['working_password']}")
            print("Update .env and render-docker.yaml with this format")
        
        return any([results['direct_auth'], results['app_config_auth'], results['email_service']])
        
    except Exception as e:
        print(f"Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
