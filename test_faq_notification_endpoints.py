#!/usr/bin/env python3
"""
Test FAQ and notification endpoints to verify real-time data fetching
"""

def test_faq_notification_endpoints():
    """Test the FAQ and notification endpoints"""
    
    from app import create_app
    from app.models import FAQRecord, Notification
    
    app = create_app()
    
    with app.app_context():
        print("=== TESTING FAQ AND NOTIFICATION ENDPOINTS ===")
        
        # Test data
        print("\n1. Checking database data:")
        faq_count = FAQRecord.query.count()
        notification_count = Notification.query.count()
        print(f"   FAQRecord count: {faq_count}")
        print(f"   Notification count: {notification_count}")
        
        # Test with test client
        with app.test_client() as client:
            print("\n2. Testing FAQ stats endpoint:")
            try:
                response = client.get('/admin/faq-records-stats')
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.get_json()
                    print(f"   Response: {data}")
                else:
                    print(f"   Error: {response.data.decode()}")
            except Exception as e:
                print(f"   Exception: {e}")
            
            print("\n3. Testing notification stats endpoint:")
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
            
            print("\n4. Testing notifications API endpoint:")
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
        
        print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    test_faq_notification_endpoints()
