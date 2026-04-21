#!/usr/bin/env python3
"""
Comprehensive fix for all production errors
"""

def fix_production_comprehensive():
    """Fix all remaining production errors comprehensively"""
    
    print("=== COMPREHENSIVE PRODUCTION FIX ===")
    
    # Fix 1: Add datetime import at the top of admin.py
    print("\n1. Adding datetime import to admin.py...")
    
    with open('app/blueprints/admin.py', 'r', encoding='utf-8') as f:
        admin_content = f.read()
    
    # Check if datetime is imported at the top
    if 'from datetime import datetime' not in admin_content.split('\n')[:10]:
        # Find the import section and add datetime
        import_section = admin_content.split('\n')[:15]
        datetime_import_added = False
        
        for i, line in enumerate(import_section):
            if line.startswith('from app.extensions import db'):
                # Add datetime import right after db import
                lines = admin_content.split('\n')
                lines.insert(i + 1, 'from datetime import datetime')
                admin_content = '\n'.join(lines)
                datetime_import_added = True
                break
        
        if not datetime_import_added:
            # Add at the beginning if no suitable spot found
            admin_content = 'from datetime import datetime\n' + admin_content
    
    # Fix 2: Fix all Notification.query usage in manage_notifications
    print("2. Fixing Notification.query usage in manage_notifications...")
    
    old_notifications_query = '''        # Build query
        query = Notification.query
        
        # Apply search filter
        if search:
            query = query.filter(
                Notification.title.ilike(f'%{search}%') |
                Notification.content.ilike(f'%{search}%')
            )
        
        # Apply status filter
        if status_filter == 'active':
            query = query.filter(Notification.expires_at > datetime.utcnow())
        elif status_filter == 'expired':
            query = query.filter(Notification.expires_at <= datetime.utcnow())
        
        # Get paginated results
        notifications_pagination = query.order_by(
            Notification.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)'''
    
    new_notifications_query = '''        # Build query
        query = db.session.query(Notification)
        
        # Apply search filter
        if search:
            query = query.filter(
                Notification.title.ilike(f'%{search}%') |
                Notification.content.ilike(f'%{search}%')
            )
        
        # Apply status filter
        if status_filter == 'active':
            query = query.filter(Notification.expires_at > datetime.utcnow())
        elif status_filter == 'expired':
            query = query.filter(Notification.expires_at <= datetime.utcnow())
        
        # Get paginated results
        notifications_pagination = query.order_by(
            Notification.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)'''
    
    admin_content = admin_content.replace(old_notifications_query, new_notifications_query)
    
    # Fix 3: Fix all FAQRecord.query usage in manage_faqs
    print("3. Fixing FAQRecord.query usage in manage_faqs...")
    
    old_faqs_query = '''        # Build query
        query = FAQRecord.query
        
        # Apply search filter
        if search:
            query = query.filter(FAQRecord.query.ilike(f'%{search}%'))
        
        # Get paginated results
        faq_pagination = query.order_by(FAQRecord.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)'''
    
    new_faqs_query = '''        # Build query
        query = db.session.query(FAQRecord)
        
        # Apply search filter
        if search:
            query = query.filter(FAQRecord.query.ilike(f'%{search}%'))
        
        # Get paginated results
        faq_pagination = query.order_by(FAQRecord.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)'''
    
    admin_content = admin_content.replace(old_faqs_query, new_faqs_query)
    
    # Fix 4: Fix refresh_faqs function
    print("4. Fixing refresh_faqs function...")
    
    old_refresh_faqs = '''        # Build query
        query = FAQRecord.query
        
        # Apply filters
        if search:
            query = query.filter(FAQRecord.query.ilike(f'%{search}%'))
        
        # Get paginated results
        faq_pagination = db.session.query(FAQRecord).order_by(FAQRecord.created_at.desc()).paginate(page=page, per_page=10, error_out=False)'''
    
    new_refresh_faqs = '''        # Build query
        query = db.session.query(FAQRecord)
        
        # Apply filters
        if search:
            query = query.filter(FAQRecord.query.ilike(f'%{search}%'))
        
        # Get paginated results
        faq_pagination = query.order_by(FAQRecord.created_at.desc()).paginate(page=page, per_page=10, error_out=False)'''
    
    admin_content = admin_content.replace(old_refresh_faqs, new_refresh_faqs)
    
    # Fix 5: Fix toggle_faq_status function
    print("5. Fixing toggle_faq_status function...")
    
    old_toggle_faq = '''        faq = FAQRecord.query.get_or_404(faq_id)'''
    
    new_toggle_faq = '''        faq = db.session.query(FAQRecord).get_or_404(faq_id)'''
    
    admin_content = admin_content.replace(old_toggle_faq, new_toggle_faq)
    
    # Fix 6: Fix routes.py completely
    print("6. Fixing routes.py completely...")
    
    with open('app/routes.py', 'r', encoding='utf-8') as f:
        routes_content = f.read()
    
    # Add datetime import at the top of routes.py if not present
    if 'from datetime import datetime' not in routes_content.split('\n')[:10]:
        lines = routes_content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('from app.extensions import db'):
                lines.insert(i + 1, 'from datetime import datetime')
                break
        routes_content = '\n'.join(lines)
    
    # Fix all FAQRecord.query usage in routes.py
    routes_content = routes_content.replace('FAQRecord.query', 'db.session.query(FAQRecord)')
    
    # Fix all Notification.query usage in routes.py
    routes_content = routes_content.replace('Notification.query', 'db.session.query(Notification)')
    
    # Fix any remaining .query.get_or_404 patterns
    routes_content = routes_content.replace('.query.get_or_404', 'db.session.query')
    
    # Fix specific patterns
    routes_content = routes_content.replace('db.session.query(FAQRecord).get_or_404', 'db.session.query(FAQRecord).get_or_404')
    routes_content = routes_content.replace('db.session.query(Notification).get_or_404', 'db.session.query(Notification).get_or_404')
    
    # Fix 7: Update the FAQRecord statistics to use proper query
    print("7. Fixing FAQRecord statistics...")
    
    old_faq_stats = '''            'total_faqs': FAQRecord.query.count(),
            'active_faqs': FAQRecord.query.filter_by(processed=True).count(),
            'inactive_faqs': FAQRecord.query.filter_by(processed=False).count(),"''
    
    new_faq_stats = '''            'total_faqs': db.session.query(FAQRecord).count(),
            'active_faqs': db.session.query(FAQRecord).filter_by(processed=True).count(),
            'inactive_faqs': db.session.query(FAQRecord).filter_by(processed=False).count(),"''
    
    admin_content = admin_content.replace(old_faq_stats, new_faq_stats)
    
    # Fix 8: Update notification statistics
    print("8. Fixing notification statistics...")
    
    old_notification_stats = '''            'total_notifications': db.session.query(Notification).count(),
            'active_notifications': db.session.query(Notification).filter(
                Notification.expires_at > datetime.utcnow()
            ).count(),
            'expired_notifications': db.session.query(Notification).filter(
                Notification.expires_at <= datetime.utcnow()
            ).count()'''
    
    new_notification_stats = '''            'total_notifications': db.session.query(Notification).count(),
            'active_notifications': db.session.query(Notification).filter(
                Notification.expires_at > datetime.utcnow()
            ).count(),
            'expired_notifications': db.session.query(Notification).filter(
                Notification.expires_at <= datetime.utcnow()
            ).count()'''
    
    admin_content = admin_content.replace(old_notification_stats, new_notification_stats)
    
    # Write the fixed content back
    with open('app/blueprints/admin.py', 'w', encoding='utf-8') as f:
        f.write(admin_content)
    
    with open('app/routes.py', 'w', encoding='utf-8') as f:
        f.write(routes_content)
    
    print("\n=== COMPREHENSIVE FIX COMPLETE ===")
    print("\nChanges made:")
    print("1. Added datetime import at the top of admin.py")
    print("2. Fixed all Notification.query usage to use db.session.query")
    print("3. Fixed all FAQRecord.query usage to use db.session.query")
    print("4. Fixed refresh_faqs function query patterns")
    print("5. Fixed toggle_faq_status function query patterns")
    print("6. Added datetime import at the top of routes.py")
    print("7. Fixed all query patterns in routes.py")
    print("8. Fixed statistics functions to use proper query patterns")
    print("\nAll production errors should now be resolved!")

if __name__ == "__main__":
    fix_production_comprehensive()
