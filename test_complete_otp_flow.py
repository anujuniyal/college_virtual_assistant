#!/usr/bin/env python3
"""
Test Complete OTP Login Flow - Simulate Web Request
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app
from app.services.optimized_otp_service import OptimizedOTPService
from app.models import Admin, Faculty
from flask import session

def test_complete_otp_flow():
    """Test the complete OTP flow as it would work in the web interface"""
    print("Testing Complete OTP Login Flow...")
    
    app = create_app()
    
    with app.test_client() as client:
        with app.app_context():
            try:
                # Test email
                test_email = "gojo976038@gmail.com"
                
                # Step 1: Check if user exists (like /send-otp route does)
                print("1. Checking if user exists...")
                admin = Admin.query.filter_by(email=test_email).first()
                faculty = Faculty.query.filter_by(email=test_email).first()
                
                if not admin and not faculty:
                    print(f"   No user found with email: {test_email}")
                    return
                
                user = admin if admin else faculty
                print(f"   Found user: {user.username if admin else user.name}")
                
                # Step 2: Send OTP (simulate /send-otp POST request)
                print("2. Sending OTP...")
                response = client.post('/send-otp', data={
                    'email': test_email
                })
                
                if response.status_code == 200:
                    result = response.get_json()
                    if result.get('success'):
                        print(f"   OTP sent successfully!")
                        if 'otp_code' in result:
                            otp_code = result['otp_code']
                            print(f"   Development OTP: {otp_code}")
                        else:
                            # Generate OTP manually to get the code for testing
                            otp_code, _ = OptimizedOTPService.generate_otp_fast(test_email)
                            print(f"   Generated OTP for testing: {otp_code}")
                    else:
                        print(f"   Failed to send OTP: {result.get('message')}")
                        return
                else:
                    print(f"   HTTP Error: {response.status_code}")
                    return
            
                # Step 3: Verify OTP (simulate /verify-otp POST request)
                print("3. Verifying OTP...")
                response = client.post('/verify-otp', data={
                    'email': test_email,
                    'otp': otp_code
                })
                
                if response.status_code == 200:
                    result = response.get_json()
                    if result.get('success'):
                        print("   OTP verification successful!")
                        print(f"   Redirect URL: {result.get('redirect')}")
                        print("   Login should work!")
                    else:
                        print(f"   OTP verification failed: {result.get('message')}")
                        print("   This is the issue!")
                        
                        # Debug: Let's check what's in the database
                        print("4. Debugging database state...")
                        from app.models import OTP
                        otp_records = OTP.query.filter_by(email=test_email).order_by(OTP.created_at.desc()).limit(5).all()
                        for i, otp_rec in enumerate(otp_records):
                            print(f"   OTP {i+1}: {otp_rec.otp_code}, Used: {otp_rec.used}, Expires: {otp_rec.expires_at}, Valid: {otp_rec.is_valid()}")
                else:
                    print(f"   HTTP Error during verification: {response.status_code}")
                    print(f"   Response: {response.get_data(as_text=True)}")
                
            except Exception as e:
                print(f"Test failed with error: {str(e)}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    test_complete_otp_flow()
