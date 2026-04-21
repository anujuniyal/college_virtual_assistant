#!/usr/bin/env python3
"""
Test script to verify remember me functionality for Render deployment
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db, login_manager
from flask import session
import json

def test_render_remember_me():
    """Test remember me functionality for Render deployment"""
    app = create_app()
    
    with app.test_request_context():
        print("🔍 Testing Remember Me Functionality for Render Deployment")
        print("=" * 60)
        
        # Test 1: Check Render-specific configuration
        print("1. Testing Render deployment configuration...")
        
        # Check if running on Render
        is_render = os.environ.get('RENDER') == 'true' or os.path.exists('/etc/render')
        print(f"   ✅ Render environment detected: {is_render}")
        
        # Check critical environment variables for remember me
        secret_key = os.environ.get('SECRET_KEY')
        flask_env = os.environ.get('FLASK_ENV')
        server_name = os.environ.get('SERVER_NAME')
        
        print(f"   ✅ SECRET_KEY configured: {'Yes' if secret_key else '❌ NO'}")
        print(f"   ✅ FLASK_ENV: {flask_env}")
        print(f"   ✅ SERVER_NAME: {server_name}")
        
        # Test 2: Check session configuration for Render
        print("\n2. Testing session configuration for Render...")
        
        session_cookie_secure = app.config.get('SESSION_COOKIE_SECURE', False)
        session_cookie_httponly = app.config.get('SESSION_COOKIE_HTTPONLY', False)
        session_cookie_samesite = app.config.get('SESSION_COOKIE_SAMESITE', None)
        remember_duration = app.config.get('REMEMBER_COOKIE_DURATION', None)
        permanent_session_lifetime = app.config.get('PERMANENT_SESSION_LIFETIME', None)
        
        print(f"   ✅ SESSION_COOKIE_SECURE: {session_cookie_secure}")
        print(f"   ✅ SESSION_COOKIE_HTTPONLY: {session_cookie_httponly}")
        print(f"   ✅ SESSION_COOKIE_SAMESITE: {session_cookie_samesite}")
        print(f"   ✅ REMEMBER_COOKIE_DURATION: {remember_duration}")
        print(f"   ✅ PERMANENT_SESSION_LIFETIME: {permanent_session_lifetime}")
        
        # Test 3: Check if configuration is Render-compatible
        print("\n3. Testing Render compatibility...")
        
        issues = []
        
        if is_render and not session_cookie_secure:
            issues.append("SESSION_COOKIE_SECURE should be True in production")
        
        if is_render and not session_cookie_httponly:
            issues.append("SESSION_COOKIE_HTTPONLY should be True in production")
        
        if not remember_duration:
            issues.append("REMEMBER_COOKIE_DURATION should be configured")
        
        if not secret_key or secret_key == 'dev-secret-key-change-in-production':
            issues.append("SECRET_KEY should be set to a secure value in production")
        
        if issues:
            print("   ❌ Configuration issues found:")
            for issue in issues:
                print(f"      - {issue}")
        else:
            print("   ✅ All Render configurations are correct")
        
        # Test 4: Test remember me functionality in Render-like environment
        print("\n4. Testing remember me functionality...")
        
        with app.test_client() as client:
            # Simulate Render environment
            with client.session_transaction() as sess:
                sess['render_test'] = True
            
            # Test login with remember me
            response = client.post('/auth/login', data={
                'username': 'test@edubot.com',
                'password': 'test123',
                'remember': 'on',
                'selected_role': 'admin'
            }, follow_redirects=False)
            
            # Check cookies
            cookies = response.headers.getlist('Set-Cookie')
            print(f"   ✅ Login response cookies: {len(cookies)}")
            
            remember_cookie_found = False
            session_cookie_found = False
            
            for cookie in cookies:
                if 'remember_token' in cookie:
                    remember_cookie_found = True
                    print("   ✅ Remember token cookie found")
                    
                    # Check cookie attributes for Render
                    if 'HttpOnly' in cookie:
                        print("   ✅ HttpOnly attribute present")
                    if 'Secure' in cookie:
                        print("   ✅ Secure attribute present (required for Render HTTPS)")
                    if 'SameSite' in cookie:
                        print("   ✅ SameSite attribute present")
                
                if 'session' in cookie:
                    session_cookie_found = True
                    print("   ✅ Session cookie found")
            
            if not remember_cookie_found:
                print("   ⚠️  Remember token cookie not found - may indicate issue")
            
            if not session_cookie_found:
                print("   ⚠️  Session cookie not found - may indicate issue")
        
        # Test 5: Check render.yaml for required environment variables
        print("\n5. Checking render.yaml configuration...")
        
        try:
            with open('render.yaml', 'r') as f:
                render_config = f.read()
            
            required_vars = [
                'SECRET_KEY',
                'FLASK_ENV',
                'DATABASE_URL'
            ]
            
            missing_vars = []
            for var in required_vars:
                if var not in render_config and var not in os.environ:
                    missing_vars.append(var)
            
            if missing_vars:
                print(f"   ⚠️  Missing environment variables in render.yaml: {missing_vars}")
                print("   💡 Add these to render.yaml envVars:")
                for var in missing_vars:
                    print(f"      - key: {var}")
                    print(f"        value: your_secure_value_here")
            else:
                print("   ✅ All required environment variables configured")
                
        except Exception as e:
            print(f"   ⚠️  Could not check render.yaml: {e}")
        
        # Test 6: Generate Render deployment recommendations
        print("\n6. Render deployment recommendations...")
        
        recommendations = []
        
        if is_render:
            if not app.config.get('REMEMBER_COOKIE_DURATION'):
                recommendations.append("Add REMEMBER_COOKIE_DURATION = timedelta(days=30) to config")
            
            if not app.config.get('SESSION_COOKIE_SECURE'):
                recommendations.append("Set SESSION_COOKIE_SECURE = True for HTTPS")
            
            if not app.config.get('SESSION_COOKIE_SAMESITE'):
                recommendations.append("Set SESSION_COOKIE_SAMESITE = 'Lax' or 'Strict'")
            
            # Check if SECRET_KEY is properly configured for Render
            if not os.environ.get('SECRET_KEY') or os.environ.get('SECRET_KEY') == 'dev-secret-key-change-in-production':
                recommendations.append("Set SECRET_KEY environment variable in render.yaml")
        
        if recommendations:
            print("   💡 Recommendations for Render deployment:")
            for rec in recommendations:
                print(f"      - {rec}")
        else:
            print("   ✅ No recommendations needed")
        
        print("\n" + "=" * 60)
        print("🎉 Render Remember Me Functionality Analysis Complete!")
        
        # Final status
        if not issues and not recommendations:
            print("✅ Remember me functionality is READY for Render deployment!")
            return True
        else:
            print("⚠️  Some configuration adjustments needed for optimal Render deployment")
            return False

if __name__ == "__main__":
    success = test_render_remember_me()
    sys.exit(0 if success else 1)
