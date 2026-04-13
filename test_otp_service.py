#!/usr/bin/env python3
"""
Test OTP Service with Resend Email
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app
from app.services.otp_service import OTPService

def test_otp_service():
    """Test OTP generation and email sending"""
    print("Testing OTP Service...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Test OTP generation
            print("1. Testing OTP generation...")
            result = OTPService.generate_otp("gojo976038@gmail.com")
            
            if result['success']:
                print(f"✅ OTP generated: {result['otp_code']}")
                print(f"✅ Email sent to: {result['email']}")
                
                # Test OTP verification
                print("2. Testing OTP verification...")
                verify_result = OTPService.verify_otp("gojo976038@gmail.com", result['otp_code'])
                
                if verify_result:
                    print("✅ OTP verification successful!")
                else:
                    print("❌ OTP verification failed")
            else:
                print(f"❌ OTP generation failed: {result['message']}")
                
        except Exception as e:
            print(f"❌ Test failed with error: {str(e)}")

if __name__ == "__main__":
    test_otp_service()
