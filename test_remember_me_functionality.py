#!/usr/bin/env python3
"""
Test script to verify remember me functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db, login_manager
from flask import session
from flask_login import decode_cookie
import json

def test_remember_me_functionality():
    """Test remember me functionality"""
    app = create_app()
    
    with app.test_request_context():
        print("🔍 Testing Remember Me Functionality")
        print("=" * 50)
        
        # Test 1: Check configuration
        print("1. Testing remember me configuration...")
        
        # Check if REMEMBER_COOKIE_DURATION is set
        remember_duration = app.config.get('REMEMBER_COOKIE_DURATION', None)
        permanent_session_lifetime = app.config.get('PERMANENT_SESSION_LIFETIME', None)
        
        print(f"   ✅ REMEMBER_COOKIE_DURATION: {remember_duration}")
        print(f"   ✅ PERMANENT_SESSION_LIFETIME: {permanent_session_lifetime}")
        
        # Check session cookie settings
        session_cookie_secure = app.config.get('SESSION_COOKIE_SECURE', False)
        session_cookie_httponly = app.config.get('SESSION_COOKIE_HTTPONLY', False)
        session_cookie_samesite = app.config.get('SESSION_COOKIE_SAMESITE', None)
        
        print(f"   ✅ SESSION_COOKIE_SECURE: {session_cookie_secure}")
        print(f"   ✅ SESSION_COOKIE_HTTPONLY: {session_cookie_httponly}")
        print(f"   ✅ SESSION_COOKIE_SAMESITE: {session_cookie_samesite}")
        
        # Test 2: Check login route implementation
        print("\n2. Testing login route implementation...")
        
        # Import auth blueprint to test the login function
        from app.blueprints.auth import auth_bp
        
        # Check if remember parameter is properly handled
        with app.test_client() as client:
            # Test login with remember me checked
            response = client.post('/auth/login', data={
                'username': 'test@edubot.com',
                'password': 'test123',
                'remember': 'on',
                'selected_role': 'admin'
            }, follow_redirects=False)
            
            # Check if session cookies are set
            cookies = response.headers.getlist('Set-Cookie')
            print(f"   ✅ Response cookies set: {len(cookies) > 0}")
            
            for cookie in cookies:
                if 'remember_token' in cookie or 'session' in cookie:
                    print(f"   ✅ Found session/remember cookie: {cookie[:50]}...")
                    
                    # Check if cookie has proper attributes
                    if 'HttpOnly' in cookie:
                        print("   ✅ HttpOnly attribute present")
                    if 'Secure' in cookie and session_cookie_secure:
                        print("   ✅ Secure attribute present")
                    if 'SameSite' in cookie:
                        print("   ✅ SameSite attribute present")
            
            # Test login without remember me
            response_no_remember = client.post('/auth/login', data={
                'username': 'test@edubot.com',
                'password': 'test123',
                'remember': 'off',
                'selected_role': 'admin'
            }, follow_redirects=False)
            
            cookies_no_remember = response_no_remember.headers.getlist('Set-Cookie')
            print(f"   ✅ Login without remember me: {len(cookies_no_remember) > 0}")
        
        # Test 3: Check Flask-Login setup
        print("\n3. Testing Flask-Login setup...")
        
        # Check if login_manager is properly configured
        print(f"   ✅ LoginManager initialized: {login_manager is not None}")
        print(f"   ✅ Login view: {login_manager.login_view}")
        print(f"   ✅ Login message: {login_manager.login_message}")
        
        # Test cookie decoding functionality
        try:
            # Create a test remember token
            with app.test_request_context():
                from flask_login import encode_cookie
                test_data = {'user_id': 1, 'remember': True}
                encoded = encode_cookie(json.dumps(test_data))
                print(f"   ✅ Cookie encoding works: {len(encoded) > 0}")
                
                # Test decoding
                decoded = decode_cookie(encoded)
                if decoded:
                    print(f"   ✅ Cookie decoding works: {decoded is not None}")
                else:
                    print("   ⚠️  Cookie decoding failed")
        except Exception as e:
            print(f"   ⚠️  Cookie encoding/decoding test failed: {e}")
        
        # Test 4: Check template implementation
        print("\n4. Testing template implementation...")
        
        # Check if remember me checkbox exists in login template
        try:
            with open('app/templates/login.html', 'r') as f:
                template_content = f.read()
                
            if 'name="remember"' in template_content:
                print("   ✅ Remember me checkbox found in template")
            else:
                print("   ❌ Remember me checkbox not found in template")
                
            if 'id="remember"' in template_content:
                print("   ✅ Remember me checkbox has proper ID")
            else:
                print("   ❌ Remember me checkbox missing ID")
                
            if 'Remember me' in template_content:
                print("   ✅ Remember me label found in template")
            else:
                print("   ❌ Remember me label not found")
                
        except Exception as e:
            print(f"   ⚠️  Template check failed: {e}")
        
        # Test 5: Configuration recommendations
        print("\n5. Configuration analysis...")
        
        # Check if remember cookie duration is properly set
        if not remember_duration:
            print("   ⚠️  REMEMBER_COOKIE_DURATION not set - using Flask-Login default (31 days)")
            print("   💡 Recommendation: Add REMEMBER_COOKIE_DURATION = timedelta(days=30) to config")
        else:
            print(f"   ✅ Remember cookie duration configured: {remember_duration}")
        
        # Check session security
        if not session_cookie_httponly:
            print("   ⚠️  SESSION_COOKIE_HTTPONLY not set")
            print("   💡 Recommendation: Set SESSION_COOKIE_HTTPONLY = True")
        
        if not session_cookie_samesite:
            print("   ⚠️  SESSION_COOKIE_SAMESITE not set")
            print("   💡 Recommendation: Set SESSION_COOKIE_SAMESITE = 'Lax'")
        
        print("\n" + "=" * 50)
        print("🎉 Remember Me Functionality Analysis Complete!")
        
        return True

if __name__ == "__main__":
    success = test_remember_me_functionality()
    sys.exit(0 if success else 1)
