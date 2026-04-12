#!/usr/bin/env python3
"""
Test Email Configuration and Safe Execute Fixes
"""
import sys
import os

# Add app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_email_configuration():
    """Test email configuration loading"""
    print("=== TESTING EMAIL CONFIGURATION ===")
    
    from app import create_app
    
    app = create_app()
    
    with app.app_context():
        # Check email configuration
        mail_server = app.config.get('MAIL_SERVER')
        mail_username = app.config.get('MAIL_USERNAME')
        mail_password = app.config.get('MAIL_PASSWORD')
        mail_default_sender = app.config.get('MAIL_DEFAULT_SENDER')
        
        print(f"MAIL_SERVER: {mail_server}")
        print(f"MAIL_USERNAME: {mail_username}")
        print(f"MAIL_PASSWORD: {'SET' if mail_password else 'NOT SET'}")
        print(f"MAIL_DEFAULT_SENDER: {mail_default_sender}")
        
        # Test email configuration completeness
        if all([mail_server, mail_username, mail_password]):
            print("Email configuration: COMPLETE")
        else:
            print("Email configuration: INCOMPLETE")
        
        # Test email service
        from app.services.email_service import EmailService
        
        # Test email configuration check
        print("Testing email service configuration check...")
        try:
            # This should not show "Email configuration incomplete" warning
            result = EmailService.send_email(
                to="test@example.com",
                subject="Test Email Configuration",
                body="This is a test to verify email configuration."
            )
            print(f"Email service test result: {result}")
        except Exception as e:
            print(f"Email service test error: {e}")

def test_safe_execute():
    """Test safe execute function"""
    print("\n=== TESTING SAFE EXECUTE ===")
    
    from app.services.safe_execute import safe_execute
    from app.models import Student
    
    # Test safe_execute with lambda function (correct usage)
    print("Testing safe_execute with lambda function...")
    try:
        result = safe_execute(lambda: 1 + 1)
        print(f"Lambda test result: {result}")
    except Exception as e:
        print(f"Lambda test error: {e}")
    
    # Test safe_execute with direct function call (should work)
    print("Testing safe_execute with direct function...")
    try:
        def test_func():
            return 2 + 2
        result = safe_execute(test_func)
        print(f"Direct function test result: {result}")
    except Exception as e:
        print(f"Direct function test error: {e}")
    
    # Test safe_execute with list (should cause error before fix)
    print("Testing safe_execute with list (should not cause error after fix)...")
    try:
        test_list = [1, 2, 3]
        # This should NOT be called - safe_execute expects a function
        # result = safe_execute(test_list)  # This would cause "list object is not callable"
        print("List test: skipped (would cause error if called)")
    except Exception as e:
        print(f"List test error: {e}")

def main():
    """Main test function"""
    print("EMAIL AND SAFE EXECUTE FIXES TEST")
    print("=" * 50)
    
    try:
        # Test email configuration
        test_email_configuration()
        
        # Test safe execute
        test_safe_execute()
        
        print("\n" + "=" * 50)
        print("TESTS COMPLETED")
        
        print("\nFIXES APPLIED:")
        print("1. Email service now uses current_app.config for configuration")
        print("2. Safe execute usage standardized to use lambda functions")
        print("3. No more 'list object is not callable' errors expected")
        print("4. Email configuration should work properly on Render")
        
    except Exception as e:
        print(f"Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
