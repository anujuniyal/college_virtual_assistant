#!/usr/bin/env python3
"""
Test Faculty Forgot Password OTP Functionality
"""
import sys
import os

# Add app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_faculty_email_lookup():
    """Test faculty email lookup for forgot password"""
    print("=== FACULTY EMAIL LOOKUP TEST ===")
    
    from app import create_app
    from app.models import Faculty, Admin
    
    app = create_app()
    
    with app.app_context():
        # Get sample faculty records
        faculty_records = Faculty.query.limit(3).all()
        admin_records = Admin.query.limit(3).all()
        
        print(f"Found {len(faculty_records)} faculty records")
        print(f"Found {len(admin_records)} admin records")
        
        if faculty_records:
            print("\nSample Faculty Records:")
            for faculty in faculty_records:
                print(f"  - {faculty.name} ({faculty.email})")
        
        if admin_records:
            print("\nSample Admin Records:")
            for admin in admin_records:
                print(f"  - {admin.username} ({admin.email})")
        
        return faculty_records, admin_records

def test_forgot_password_flow():
    """Test forgot password flow for faculty"""
    print("\n=== FORGOT PASSWORD FLOW TEST ===")
    
    from app import create_app
    from app.models import Faculty, Admin
    from app.services.otp_service import OTPService
    
    app = create_app()
    
    with app.app_context():
        # Get a test faculty member
        test_faculty = Faculty.query.first()
        
        if not test_faculty:
            print("No faculty records found for testing")
            return False
        
        print(f"Testing with faculty: {test_faculty.name} ({test_faculty.email})")
        
        try:
            # Test OTP generation for faculty email
            otp_result = OTPService.generate_otp(test_faculty.email)
            otp_code = otp_result[0] if isinstance(otp_result, tuple) else otp_result
            email_sent = otp_result[1] if isinstance(otp_result, tuple) else False
            
            print(f"OTP generated: {otp_code}")
            print(f"Email sent to: {test_faculty.email}")
            print(f"Email delivery: {'SUCCESS' if email_sent else 'FAILED'}")
            
            # Test OTP verification
            verified = OTPService.verify_otp(test_faculty.email, otp_code)
            print(f"OTP verification: {'SUCCESS' if verified else 'FAILED'}")
            
            return email_sent and verified
            
        except Exception as e:
            print(f"Forgot password test error: {e}")
            return False

def test_admin_forgot_password_flow():
    """Test forgot password flow for admin"""
    print("\n=== ADMIN FORGOT PASSWORD FLOW TEST ===")
    
    from app import create_app
    from app.models import Admin
    from app.services.otp_service import OTPService
    
    app = create_app()
    
    with app.app_context():
        # Get a test admin
        test_admin = Admin.query.first()
        
        if not test_admin:
            print("No admin records found for testing")
            return False
        
        print(f"Testing with admin: {test_admin.username} ({test_admin.email})")
        
        try:
            # Test OTP generation for admin email
            otp_result = OTPService.generate_otp(test_admin.email)
            otp_code = otp_result[0] if isinstance(otp_result, tuple) else otp_result
            email_sent = otp_result[1] if isinstance(otp_result, tuple) else False
            
            print(f"OTP generated: {otp_code}")
            print(f"Email sent to: {test_admin.email}")
            print(f"Email delivery: {'SUCCESS' if email_sent else 'FAILED'}")
            
            # Test OTP verification
            verified = OTPService.verify_otp(test_admin.email, otp_code)
            print(f"OTP verification: {'SUCCESS' if verified else 'FAILED'}")
            
            return email_sent and verified
            
        except Exception as e:
            print(f"Admin forgot password test error: {e}")
            return False

def test_email_validation_logic():
    """Test email validation logic from forgot password route"""
    print("\n=== EMAIL VALIDATION LOGIC TEST ===")
    
    from app import create_app
    from app.models import Faculty, Admin
    
    app = create_app()
    
    with app.app_context():
        # Test cases
        test_emails = [
            "nonexistent@example.com",  # Should fail
        ]
        
        # Add existing emails
        faculty = Faculty.query.first()
        admin = Admin.query.first()
        
        if faculty:
            test_emails.append(faculty.email)
        if admin:
            test_emails.append(admin.email)
        
        results = {}
        
        for email in test_emails:
            print(f"\nTesting email: {email}")
            
            # Check if email exists in Admin or Faculty tables (same logic as forgot password)
            admin = Admin.query.filter_by(email=email).first()
            faculty = Faculty.query.filter_by(email=email).first()
            
            if admin:
                print(f"  Found in Admin table: {admin.username}")
                results[email] = {'found': True, 'type': 'admin', 'user': admin.username}
            elif faculty:
                print(f"  Found in Faculty table: {faculty.name}")
                results[email] = {'found': True, 'type': 'faculty', 'user': faculty.name}
            else:
                print(f"  Not found in system")
                results[email] = {'found': False, 'type': None, 'user': None}
        
        return results

def test_otp_email_content():
    """Test OTP email content format"""
    print("\n=== OTP EMAIL CONTENT TEST ===")
    
    from app import create_app
    from app.services.email_service import EmailService
    
    app = create_app()
    
    with app.app_context():
        try:
            # Test OTP email format
            test_otp = "123456"
            test_email = "test-faculty@example.com"
            
            otp_email_body = f"""
            Your OTP is: {test_otp}
            
            This OTP will expire in 10 minutes.
            
            If you didn't request this OTP, please ignore this email.
            """
            
            result = EmailService.send_email(
                to=test_email,
                subject="Your OTP for College Virtual Assistant",
                body=otp_email_body
            )
            
            print(f"OTP email test result: {'SUCCESS' if result else 'FAILED'}")
            print(f"Email sent to: {test_email}")
            print(f"OTP in email: {test_otp}")
            
            return result
            
        except Exception as e:
            print(f"OTP email content test error: {e}")
            return False

def main():
    """Main test function"""
    print("FACULTY FORGOT PASSWORD OTP VERIFICATION")
    print("=" * 50)
    
    results = {
        'email_lookup': False,
        'faculty_forgot': False,
        'admin_forgot': False,
        'email_validation': False,
        'otp_content': False
    }
    
    try:
        # Test email lookup
        faculty_records, admin_records = test_faculty_email_lookup()
        results['email_lookup'] = len(faculty_records) > 0 or len(admin_records) > 0
        
        # Test faculty forgot password flow
        if faculty_records:
            results['faculty_forgot'] = test_forgot_password_flow()
        
        # Test admin forgot password flow
        if admin_records:
            results['admin_forgot'] = test_admin_forgot_password_flow()
        
        # Test email validation logic
        validation_results = test_email_validation_logic()
        results['email_validation'] = any(result['found'] for result in validation_results.values())
        
        # Test OTP email content
        results['otp_content'] = test_otp_email_content()
        
        print("\n" + "=" * 50)
        print("FACULTY FORGOT PASSWORD TEST RESULTS")
        print("=" * 50)
        
        for test, result in results.items():
            status = "PASS" if result else "FAIL"
            print(f"{test.replace('_', ' ').title()}: {status}")
        
        # Overall status
        all_passed = all(results.values())
        print(f"\nOverall Status: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
        
        if all_passed:
            print("\nFORGOT PASSWORD FUNCTIONALITY: WORKING CORRECTLY")
            print("OTPs are sent to the registered email addresses of faculty and admin users")
        else:
            print("\nISSUES FOUND:")
            for test, result in results.items():
                if not result:
                    print(f"  - {test.replace('_', ' ').title()}: FAILED")
        
        # Show validation results
        print("\nEMAIL VALIDATION RESULTS:")
        for email, result in validation_results.items():
            if result['found']:
                print(f"  {email}: FOUND ({result['type']} - {result['user']})")
            else:
                print(f"  {email}: NOT FOUND")
        
        return all_passed
        
    except Exception as e:
        print(f"Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
