#!/usr/bin/env python3
"""
Test the production fixes for FAQ and notification errors
"""

def test_production_fixes():
    """Test the fixes for production errors"""
    
    from app import create_app
    from app.models import FAQRecord, Notification
    from app.extensions import db
    from datetime import datetime
    
    app = create_app()
    
    with app.app_context():
        print("=== TESTING PRODUCTION FIXES ===")
        
        # Test 1: FAQRecord query with proper db.session.query
        print("\n1. Testing FAQRecord query fixes:")
        try:
            # Test the query pattern used in the fixed code
            faq_query = db.session.query(FAQRecord).order_by(FAQRecord.created_at.desc())
            faq_count = faq_query.count()
            faq_results = faq_query.limit(3).all()
            
            print(f"   FAQRecord query successful: {faq_count} records found")
            print(f"   First 3 records:")
            for faq in faq_results:
                print(f"     - ID: {faq.id}, Query: {faq.query[:30]}..., Created: {faq.created_at}")
                
        except Exception as e:
            print(f"   ERROR: {e}")
        
        # Test 2: Notification query with datetime
        print("\n2. Testing notification query with datetime:")
        try:
            # Test the query pattern used in the fixed code
            now = datetime.utcnow()
            active_notifications = db.session.query(Notification).filter(
                Notification.expires_at > now
            ).count()
            expired_notifications = db.session.query(Notification).filter(
                Notification.expires_at <= now
            ).count()
            total_notifications = db.session.query(Notification).count()
            
            print(f"   Notification query successful:")
            print(f"   - Total: {total_notifications}")
            print(f"   - Active: {active_notifications}")
            print(f"   - Expired: {expired_notifications}")
            
        except Exception as e:
            print(f"   ERROR: {e}")
        
        # Test 3: Pagination query
        print("\n3. Testing pagination query:")
        try:
            # Test pagination pattern used in the fixed code
            page = 1
            per_page = 10
            faq_pagination = db.session.query(FAQRecord).order_by(FAQRecord.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
            
            print(f"   Pagination query successful:")
            print(f"   - Total items: {faq_pagination.total}")
            print(f"   - Pages: {faq_pagination.pages}")
            print(f"   - Current page items: {len(faq_pagination.items)}")
            
        except Exception as e:
            print(f"   ERROR: {e}")
        
        print("\n=== TEST COMPLETE ===")
        print("\nIf all tests passed, the production fixes should work correctly!")

if __name__ == "__main__":
    test_production_fixes()
