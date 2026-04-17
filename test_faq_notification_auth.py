#!/usr/bin/env python3
"""
Test FAQ and notification endpoints with authentication
"""

def test_faq_notification_endpoints_with_auth():
    """Test the FAQ and notification endpoints with proper authentication"""
    
    from app import create_app
    from app.models import FAQRecord, Notification, Admin
    from app.extensions import db
    from flask import session
    
    app = create_app()
    
    with app.app_context():
        print("=== TESTING FAQ AND NOTIFICATION ENDPOINTS WITH AUTH ===")
        
        # Test data
        print("\n1. Checking database data:")
        faq_count = db.session.query(FAQRecord).count()
        notification_count = db.session.query(Notification).count()
        admin_count = db.session.query(Admin).count()
        print(f"   FAQRecord count: {faq_count}")
        print(f"   Notification count: {notification_count}")
        print(f"   Admin count: {admin_count}")
        
        # Test with test client and simulate login
        with app.test_client() as client:
            print("\n2. Testing FAQ stats endpoint with auth:")
            try:
                # Simulate admin session
                with client.session_transaction() as sess:
                    sess['user_id'] = 1  # Assuming admin ID is 1
                    sess['user_role'] = 'admin'
                    sess['user_name'] = 'admin'
                    sess['_fresh'] = True
                
                response = client.get('/admin/faq-records-stats')
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.get_json()
                    print(f"   Response: {data}")
                else:
                    print(f"   Error: {response.data.decode()}")
            except Exception as e:
                print(f"   Exception: {e}")
            
            print("\n3. Testing notification stats endpoint with auth:")
            try:
                response = client.get('/admin/notifications-stats')
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.get_json()
                    print(f"   Response: {data}")
                else:
                    print(f"   Error: {response.data.decode()}")
            except Exception as e:
                print(f"   Exception: {e}")
            
            print("\n4. Testing notifications API endpoint with auth:")
            try:
                response = client.get('/api/notifications-realtime')
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.get_json()
                    print(f"   Response: {data}")
                else:
                    print(f"   Error: {response.data.decode()}")
            except Exception as e:
                print(f"   Exception: {e}")
            
            print("\n5. Testing refresh FAQs endpoint with auth:")
            try:
                response = client.post('/admin/refresh-faqs', 
                                     json={'page': 1, 'search': '', 'category': '', 'priority': ''})
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.get_json()
                    print(f"   Response: {data}")
                else:
                    print(f"   Error: {response.data.decode()}")
            except Exception as e:
                print(f"   Exception: {e}")
        
        print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    test_faq_notification_endpoints_with_auth()
