#!/usr/bin/env python3
"""
Debug OTP Login Flow
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app
from app.services.optimized_otp_service import OptimizedOTPService
from app.models import Admin, Faculty

def debug_otp_login():
    """Debug the complete OTP login flow"""
    print("Debugging OTP Login Flow...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Test email
            test_email = "gojo976038@gmail.com"
            
            # Check if user exists
            print("1. Checking if user exists...")
            admin = Admin.query.filter_by(email=test_email).first()
            faculty = Faculty.query.filter_by(email=test_email).first()
            
            if admin:
                print(f"   Found Admin: {admin.username} (Role: {admin.role})")
            elif faculty:
                print(f"   Found Faculty: {faculty.name} (Role: {faculty.role})")
            else:
                print(f"   No user found with email: {test_email}")
                return
            
            # Generate OTP using optimized service (like /send-otp route)
            print("2. Generating OTP using OptimizedOTPService...")
            otp_code, email_sent = OptimizedOTPService.generate_otp_fast(test_email)
            
            if email_sent:
                print(f"   OTP generated: {otp_code}")
                print(f"   Email sent successfully")
            else:
                print("   Failed to send OTP")
                return
            
            # Verify OTP using optimized service (like /verify-otp route)
            print("3. Verifying OTP using OptimizedOTPService...")
            verify_result = OptimizedOTPService.verify_otp_fast(test_email, otp_code)
            
            if verify_result:
                print("   OTP verification successful!")
                print("   Login should work")
            else:
                print("   OTP verification failed!")
                print("   This is the issue causing login failure")
                
                # Let's try with the regular service for comparison
                print("4. Testing with regular OTPService...")
                from app.services.otp_service import OTPService
                
                # Generate new OTP with regular service
                otp_code2, email_sent2 = OTPService.generate_otp(test_email)
                if email_sent2:
                    print(f"   Regular service OTP: {otp_code2}")
                    
                    # Verify with regular service
                    verify_result2 = OTPService.verify_otp(test_email, otp_code2)
                    if verify_result2:
                        print("   Regular service verification works!")
                    else:
                        print("   Regular service verification also fails")
                
        except Exception as e:
            print(f"Debug failed with error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_otp_login()
