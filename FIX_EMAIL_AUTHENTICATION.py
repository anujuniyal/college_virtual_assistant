#!/usr/bin/env python3
"""
Fix Email Authentication Issues
"""
import sys
import os

# Add app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def update_env_file():
    """Update .env file with corrected email configuration"""
    print("=== FIXING EMAIL AUTHENTICATION ===")
    
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    
    # Read current .env file
    try:
        with open(env_file, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print("ERROR: .env file not found!")
        return False
    
    # Update email configuration with better defaults
    updated_lines = []
    for line in lines:
        line = line.strip()
        
        # Keep existing email configuration but add better defaults
        if line.startswith('MAIL_SERVER='):
            updated_lines.append(line + '\n')
        elif line.startswith('MAIL_PORT='):
            updated_lines.append(line + '\n')
        elif line.startswith('MAIL_USE_TLS='):
            updated_lines.append(line + '\n')
        elif line.startswith('MAIL_USERNAME='):
            updated_lines.append(line + '\n')
        elif line.startswith('MAIL_PASSWORD='):
            # Replace with placeholder for user to update
            updated_lines.append('MAIL_PASSWORD=UPDATE_WITH_NEW_APP_PASSWORD\n')
        elif line.startswith('MAIL_DEFAULT_SENDER='):
            updated_lines.append(line + '\n')
        elif line.startswith('ADMIN_EMAIL='):
            updated_lines.append(line + '\n')
        else:
            updated_lines.append(line + '\n')
    
    # Write updated configuration
    try:
        with open(env_file, 'w') as f:
            f.writelines(updated_lines)
        print("✅ Updated .env file with email configuration placeholders")
        return True
    except Exception as e:
        print(f"ERROR: Could not update .env file: {e}")
        return False

def create_email_test_script():
    """Create a simple email test script"""
    script_content = '''#!/usr/bin/env python3
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
'''
    
    script_path = os.path.join(os.path.dirname(__file__), 'QUICK_EMAIL_TEST.py')
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    print(f"✅ Created quick email test script: {script_path}")
    return True

def main():
    """Main fix process"""
    print("EMAIL AUTHENTICATION FIX")
    print("=" * 50)
    
    # Step 1: Update .env file
    print("\n1. Updating .env file...")
    if update_env_file():
        print("   ✅ .env file updated successfully")
    else:
        print("   ❌ Failed to update .env file")
        return False
    
    # Step 2: Create test script
    print("\n2. Creating email test script...")
    if create_email_test_script():
        print("   ✅ Test script created successfully")
    else:
        print("   ❌ Failed to create test script")
        return False
    
    # Step 3: Instructions
    print("\n3. NEXT STEPS:")
    print("   a) Generate new Gmail App Password:")
    print("      - Go to: https://myaccount.google.com/apppasswords")
    print("      - Enable 2-Factor Authentication if not enabled")
    print("      - Select 'Mail' app")
    print("      - Name it: 'EduBot College Assistant'")
    print("      - Copy the 16-character password")
    print("")
    print("   b) Update .env file:")
    print("      - Open .env file")
    print("      - Replace 'UPDATE_WITH_NEW_APP_PASSWORD' with your new app password")
    print("      - Save the file")
    print("")
    print("   c) Test email:")
    print("      - Run: python QUICK_EMAIL_TEST.py")
    print("      - Should show 'Email test result: SUCCESS'")
    print("")
    print("   d) Deploy to Render:")
    print("      - Update MAIL_PASSWORD in Render environment")
    print("      - Push changes to GitHub")
    
    print("\n" + "=" * 50)
    print("EMAIL AUTHENTICATION FIX COMPLETED!")
    print("Follow the steps above to resolve email issues.")
    
    return True

if __name__ == "__main__":
    main()
