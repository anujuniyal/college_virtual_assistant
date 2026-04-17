#!/usr/bin/env python3
"""
Test the comprehensive production fixes
"""

def test_comprehensive_fix():
    """Test the comprehensive fixes for production errors"""
    
    from app import create_app
    from app.models import FAQRecord, Notification
    from app.extensions import db
    from datetime import datetime
    
    app = create_app()
    
    with app.app_context():
        print("=== TESTING COMPREHENSIVE PRODUCTION FIXES ===")
        
        # Test 1: FAQRecord query patterns
        print("\n1. Testing FAQRecord query patterns:")
        try:
            # Test the query pattern used in manage_faqs
            query = db.session.query(FAQRecord)
            search = 'test'
            if search:
                query = query.filter(FAQRecord.query.ilike(f'%{search}%'))
            
            faq_pagination = query.order_by(FAQRecord.created_at.desc()).paginate(page=1, per_page=10, error_out=False)
            
            print(f"   FAQRecord query pattern successful: {faq_pagination.total} records found")
            
            # Test toggle_faq_status pattern
            faq = db.session.query(FAQRecord).get_or_404(1)
            print(f"   FAQRecord get_or_404 pattern successful: {faq.id}")
            
        except Exception as e:
            print(f"   ERROR: {e}")
        
        # Test 2: Notification query patterns
        print("\n2. Testing notification query patterns:")
        try:
            # Test the query pattern used in manage_notifications
            query = db.session.query(Notification)
            
            # Test status filter
            query = query.filter(Notification.expires_at > datetime.utcnow())
            notifications_pagination = query.order_by(Notification.created_at.desc()).paginate(page=1, per_page=15, error_out=False)
            
            print(f"   Notification query pattern successful: {notifications_pagination.total} records found")
            
        except Exception as e:
            print(f"   ERROR: {e}")
        
        # Test 3: Statistics patterns
        print("\n3. Testing statistics patterns:")
        try:
            # Test FAQRecord statistics
            total_faqs = db.session.query(FAQRecord).count()
            active_faqs = db.session.query(FAQRecord).filter_by(processed=True).count()
            inactive_faqs = db.session.query(FAQRecord).filter_by(processed=False).count()
            
            print(f"   FAQRecord statistics successful:")
            print(f"   - Total: {total_faqs}, Active: {active_faqs}, Inactive: {inactive_faqs}")
            
            # Test notification statistics
            total_notifications = db.session.query(Notification).count()
            active_notifications = db.session.query(Notification).filter(
                Notification.expires_at > datetime.utcnow()
            ).count()
            expired_notifications = db.session.query(Notification).filter(
                Notification.expires_at <= datetime.utcnow()
            ).count()
            
            print(f"   Notification statistics successful:")
            print(f"   - Total: {total_notifications}, Active: {active_notifications}, Expired: {expired_notifications}")
            
        except Exception as e:
            print(f"   ERROR: {e}")
        
        # Test 4: Refresh patterns
        print("\n4. Testing refresh patterns:")
        try:
            # Test refresh_faqs pattern
            query = db.session.query(FAQRecord)
            search = ''
            if search:
                query = query.filter(FAQRecord.query.ilike(f'%{search}%'))
            
            faq_pagination = query.order_by(FAQRecord.created_at.desc()).paginate(page=1, per_page=10, error_out=False)
            
            print(f"   Refresh FAQ pattern successful: {faq_pagination.total} records")
            
        except Exception as e:
            print(f"   ERROR: {e}")
        
        print("\n=== TEST COMPLETE ===")
        print("\nIf all tests passed, the comprehensive production fixes should work correctly!")

if __name__ == "__main__":
    test_comprehensive_fix()
