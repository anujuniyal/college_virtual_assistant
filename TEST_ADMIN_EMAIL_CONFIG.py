#!/usr/bin/env python3
"""
Test Admin Email Configuration for Weekly Reports
"""
import sys
import os

# Add app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_admin_email_config():
    """Test admin email configuration in all environments"""
    print("=== ADMIN EMAIL CONFIGURATION TEST ===")
    
    from app import create_app
    
    app = create_app()
    
    with app.app_context():
        # Get admin email configuration
        admin_email = app.config.get('ADMIN_EMAIL')
        default_admin_email = app.config.get('DEFAULT_ADMIN_EMAIL')
        
        print(f"ADMIN_EMAIL: {admin_email}")
        print(f"DEFAULT_ADMIN_EMAIL: {default_admin_email}")
        
        # Test which email would be used for weekly reports
        weekly_report_email = admin_email or default_admin_email
        print(f"Weekly reports will be sent to: {weekly_report_email}")
        
        # Verify it's the correct email
        if weekly_report_email == "uniyalanuj1@gmail.com":
            print("SUCCESS: Admin email configured correctly for weekly reports")
            return True
        else:
            print("ERROR: Admin email not configured correctly")
            return False

def test_weekly_report_to_admin():
    """Test sending weekly report to admin email"""
    print("\n=== WEEKLY REPORT TO ADMIN EMAIL TEST ===")
    
    from app import create_app
    from app.services.email_service import EmailService
    
    app = create_app()
    
    with app.app_context():
        try:
            # Get admin email
            admin_email = app.config.get('ADMIN_EMAIL') or app.config.get('DEFAULT_ADMIN_EMAIL')
            
            # Test weekly report email content
            weekly_report_content = """
            WEEKLY ANALYTICS REPORT - College Virtual Assistant
            
            Generated at: Just now
            
            ADMIN EMAIL TEST:
            This report is being sent to verify admin email configuration.
            
            Target Admin Email: {}
            
            SYSTEM STATISTICS:
            - Total Students: 150
            - Total Faculty: 25
            - Total Notifications: 45
            - Active Notifications: 12
            - Total Complaints: 8
            - Pending Complaints: 3
            - Total Results: 200
            
            This is a test to verify weekly reports are sent to the correct admin email.
            """.format(admin_email)
            
            # Send test weekly report
            result = EmailService.send_email(
                to=admin_email,
                subject="Weekly Report Test - Admin Email Verification",
                body=weekly_report_content
            )
            
            print(f"Weekly report test result: {'SUCCESS' if result else 'FAILED'}")
            print(f"Test email sent to: {admin_email}")
            
            return result
            
        except Exception as e:
            print(f"Weekly report test error: {e}")
            return False

def verify_all_config_files():
    """Verify admin email in all configuration files"""
    print("\n=== CONFIGURATION FILES VERIFICATION ===")
    
    config_files = {
        '.env': os.path.join(os.path.dirname(__file__), '.env'),
        '.env.render': os.path.join(os.path.dirname(__file__), '.env.render'),
        'render-docker.yaml': os.path.join(os.path.dirname(__file__), 'render-docker.yaml')
    }
    
    all_correct = True
    
    for filename, filepath in config_files.items():
        print(f"\nChecking {filename}...")
        
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Check for ADMIN_EMAIL configuration
            if 'ADMIN_EMAIL=uniyalanuj1@gmail.com' in content:
                print(f"  ADMIN_EMAIL: CORRECT (uniyalanuj1@gmail.com)")
            elif 'ADMIN_EMAIL:' in content and 'uniyalanuj1@gmail.com' in content:
                print(f"  ADMIN_EMAIL: CORRECT (uniyalanuj1@gmail.com)")
            elif 'ADMIN_EMAIL' in content:
                print(f"  ADMIN_EMAIL: FOUND but may be incorrect")
                all_correct = False
            else:
                print(f"  ADMIN_EMAIL: NOT FOUND")
                all_correct = False
        else:
            print(f"  File not found: {filepath}")
            all_correct = False
    
    return all_correct

def main():
    """Main test function"""
    print("ADMIN EMAIL CONFIGURATION VERIFICATION")
    print("=" * 50)
    
    results = {
        'config_test': False,
        'weekly_report_test': False,
        'config_files': False
    }
    
    try:
        # Test admin email configuration
        results['config_test'] = test_admin_email_config()
        
        # Test weekly report to admin
        if results['config_test']:
            results['weekly_report_test'] = test_weekly_report_to_admin()
        
        # Verify all config files
        results['config_files'] = verify_all_config_files()
        
        print("\n" + "=" * 50)
        print("ADMIN EMAIL CONFIGURATION RESULTS")
        print("=" * 50)
        
        for test, result in results.items():
            status = "PASS" if result else "FAIL"
            print(f"{test.replace('_', ' ').title()}: {status}")
        
        # Overall status
        all_passed = all(results.values())
        print(f"\nOverall Status: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
        
        if all_passed:
            print("\nWeekly reports will be sent to: uniyalanuj1@gmail.com")
            print("Admin email configuration is complete and correct!")
        else:
            print("\nISSUES FOUND:")
            for test, result in results.items():
                if not result:
                    print(f"  - {test.replace('_', ' ').title()}: FAILED")
        
        return all_passed
        
    except Exception as e:
        print(f"Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
