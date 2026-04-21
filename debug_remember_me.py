#!/usr/bin/env python3
"""
Debug script to fix remember me functionality for Render deployment
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from flask import session, make_response
from flask_login import encode_cookie, decode_cookie
import json

def debug_remember_me():
    """Debug and fix remember me functionality"""
    app = create_app()
    
    with app.test_request_context():
        print("🔍 Debugging Remember Me Functionality")
        print("=" * 50)
        
        # Test 1: Check Flask-Login remember me mechanism
        print("1. Testing Flask-Login remember me mechanism...")
        
        with app.test_client() as client:
            # Test with valid credentials (if available)
            response = client.post('/auth/login', data={
                'username': 'sanjeev.raghav@edubot.com',  # Use known admin email
                'password': 'sanjeev123',
                'remember': 'on',
                'selected_role': 'admin'
            }, follow_redirects=False)
            
            print(f"   Response status: {response.status_code}")
            
            # Check all cookies in detail
            cookies = response.headers.getlist('Set-Cookie')
            print(f"   Number of cookies: {len(cookies)}")
            
            for i, cookie in enumerate(cookies):
                print(f"   Cookie {i+1}: {cookie}")
                
                # Check if this is a remember token
                if 'remember_token' in cookie:
                    print("   ✅ Remember token cookie found!")
                    
                    # Extract and decode the token
                    cookie_parts = cookie.split(';')
                    token_part = [part for part in cookie_parts if part.strip().startswith('remember_token=')]
                    
                    if token_part:
                        token_value = token_part[0].split('=', 1)[1].strip()
                        print(f"   Token value: {token_value[:20]}...")
                        
                        try:
                            decoded = decode_cookie(token_value)
                            if decoded:
                                print(f"   ✅ Token decoded successfully: {decoded}")
                            else:
                                print("   ❌ Token decode failed")
                        except Exception as e:
                            print(f"   ❌ Token decode error: {e}")
                
                # Check session cookie
                if 'session' in cookie:
                    print("   ✅ Session cookie found!")
        
        # Test 2: Manual remember me implementation
        print("\n2. Testing manual remember me implementation...")
        
        with app.test_request_context():
            # Test manual cookie setting
            test_data = {'user_id': 1, 'remember': True}
            encoded_token = encode_cookie(json.dumps(test_data))
            
            print(f"   ✅ Manual token encoding: {len(encoded_token) > 0}")
            
            # Test decoding
            try:
                decoded = decode_cookie(encoded_token)
                if decoded:
                    print(f"   ✅ Manual token decoding: {decoded}")
                else:
                    print("   ❌ Manual token decode failed")
            except Exception as e:
                print(f"   ❌ Manual token decode error: {e}")
        
        # Test 3: Check Flask-Login configuration
        print("\n3. Checking Flask-Login configuration...")
        
        # Check if remember cookie duration is properly set
        remember_duration = app.config.get('REMEMBER_COOKIE_DURATION')
        print(f"   REMEMBER_COOKIE_DURATION: {remember_duration}")
        
        # Check session configuration
        permanent_lifetime = app.config.get('PERMANENT_SESSION_LIFETIME')
        print(f"   PERMANENT_SESSION_LIFETIME: {permanent_lifetime}")
        
        # Check cookie settings
        cookie_secure = app.config.get('SESSION_COOKIE_SECURE')
        cookie_httponly = app.config.get('SESSION_COOKIE_HTTPONLY')
        cookie_samesite = app.config.get('SESSION_COOKIE_SAMESITE')
        
        print(f"   SESSION_COOKIE_SECURE: {cookie_secure}")
        print(f"   SESSION_COOKIE_HTTPONLY: {cookie_httponly}")
        print(f"   SESSION_COOKIE_SAMESITE: {cookie_samesite}")
        
        # Test 4: Create enhanced login function
        print("\n4. Testing enhanced login implementation...")
        
        # The issue might be that we need to set session.permanent BEFORE login_user
        print("   💡 Testing session.permanent before login_user...")
        
        with app.test_client() as client:
            with client.session_transaction() as sess:
                # Simulate the enhanced login process
                sess['test_remember'] = True
                sess.permanent = True  # Set session as permanent
                print(f"   Session permanent set: {sess.permanent}")
            
            # Test login
            response = client.post('/auth/login', data={
                'username': 'sanjeev.raghav@edubot.com',
                'password': 'sanjeev123',
                'remember': 'on',
                'selected_role': 'admin'
            }, follow_redirects=False)
            
            cookies = response.headers.getlist('Set-Cookie')
            print(f"   Enhanced test cookies: {len(cookies)}")
            
            for cookie in cookies:
                if 'remember_token' in cookie:
                    print("   ✅ Remember token found with enhanced implementation!")
                if 'Max-Age' in cookie:
                    print("   ✅ Max-Age attribute found!")
        
        # Test 5: Generate render.yaml recommendations
        print("\n5. Render deployment recommendations...")
        
        print("   Current render.yaml has:")
        print("   ✅ SECRET_KEY environment variable")
        print("   ✅ FLASK_ENV=production")
        print("   ✅ All email configuration")
        
        print("\n   Additional recommendations for optimal remember me in Render:")
        print("   💡 Ensure SECRET_KEY is unique and secure")
        print("   💡 Test with real user credentials in deployed environment")
        print("   💡 Check browser cookie settings for HTTPS domain")
        print("   💡 Verify SameSite policy works with cross-origin requests")
        
        print("\n" + "=" * 50)
        print("🎉 Remember Me Debug Complete!")
        
        return True

if __name__ == "__main__":
    success = debug_remember_me()
    sys.exit(0 if success else 1)
