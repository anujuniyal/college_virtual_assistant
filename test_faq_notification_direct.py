#!/usr/bin/env python3
"""
Test FAQ and notification database queries directly
"""

def test_faq_notification_direct():
    """Test the FAQ and notification database queries directly"""
    
    from app import create_app
    from app.models import FAQRecord, Notification
    from app.extensions import db
    from datetime import datetime
    
    app = create_app()
    
    with app.app_context():
        print("=== TESTING FAQ AND NOTIFICATION DATABASE QUERIES ===")
        
        # Test data
        print("\n1. Checking database data:")
        faq_count = db.session.query(FAQRecord).count()
        notification_count = db.session.query(Notification).count()
        print(f"   FAQRecord count: {faq_count}")
        print(f"   Notification count: {notification_count}")
        
        # Test FAQ statistics query (same as in the endpoint)
        print("\n2. Testing FAQ statistics query:")
        try:
            stats = {
                'total_faqs': db.session.query(FAQRecord).count(),
                'active_faqs': db.session.query(FAQRecord).filter_by(processed=True).count(),
                'inactive_faqs': db.session.query(FAQRecord).filter_by(processed=False).count(),
                'total_views': 0,  # FAQRecord doesn't have view_count field
                'high_priority': 0,  # FAQRecord doesn't have priority field
                'medium_priority': 0,  # FAQRecord doesn't have priority field
                'low_priority': 0,  # FAQRecord doesn't have priority field
            }
            print(f"   FAQ Stats: {stats}")
        except Exception as e:
            print(f"   Exception: {e}")
        
        # Test notification statistics query (same as in the endpoint)
        print("\n3. Testing notification statistics query:")
        try:
            stats = {
                'total_notifications': db.session.query(Notification).count(),
                'active_notifications': db.session.query(Notification).filter(
                    Notification.expires_at > datetime.utcnow()
                ).count(),
                'expired_notifications': db.session.query(Notification).filter(
                    Notification.expires_at <= datetime.utcnow()
                ).count()
            }
            print(f"   Notification Stats: {stats}")
        except Exception as e:
            print(f"   Exception: {e}")
        
        # Test FAQ refresh query (same as in the endpoint)
        print("\n4. Testing FAQ refresh query:")
        try:
            page = 1
            search = ''
            query = db.session.query(FAQRecord)
            
            # Apply search filter
            if search:
                query = query.filter(FAQRecord.query.ilike(f'%{search}%'))
            
            # Get paginated results
            faq_pagination = query.order_by(FAQRecord.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
            
            print(f"   FAQ Pagination: Total items: {faq_pagination.total}, Pages: {faq_pagination.pages}")
            print(f"   First few items:")
            for item in faq_pagination.items[:3]:
                print(f"     - ID: {item.id}, Query: {item.query[:50]}..., Processed: {item.processed}")
        except Exception as e:
            print(f"   Exception: {e}")
        
        # Test notifications API query (same as in the endpoint)
        print("\n5. Testing notifications API query:")
        try:
            notifications_data = db.session.query(Notification).order_by(Notification.created_at.desc()).all()
            
            notifications_list = []
            for notification in notifications_data:
                notifications_list.append({
                    'id': notification.id,
                    'title': notification.title,
                    'content': notification.content,
                    'link_url': notification.link_url,
                    'file_url': notification.file_url,
                    'priority': notification.priority,
                    'created_at': notification.created_at.isoformat() if notification.created_at else None,
                    'expires_at': notification.expires_at.isoformat() if notification.expires_at else None,
                    'created_by_name': 'Admin',  # Simplified for test
                    'notification_type': notification.notification_type
                })
            
            print(f"   Notifications API Data: Count: {len(notifications_list)}")
            if notifications_list:
                print(f"   First notification: {notifications_list[0]}")
        except Exception as e:
            print(f"   Exception: {e}")
        
        print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    test_faq_notification_direct()
