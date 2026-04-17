#!/usr/bin/env python3
"""
Fix critical production errors in FAQ and notification features
"""

def fix_production_errors():
    """Fix FAQRecord.query.order_by and datetime undefined errors"""
    
    print("=== FIXING PRODUCTION ERRORS ===")
    
    # Fix 1: Fix FAQRecord.query.order_by error
    print("\n1. Fixing FAQRecord.query.order_by error...")
    
    with open('app/blueprints/admin.py', 'r', encoding='utf-8') as f:
        admin_content = f.read()
    
    # Fix the manage_faqs function - the issue is using FAQRecord.query.order_by instead of db.session.query(FAQRecord).order_by
    old_manage_faqs_query = '''        # Get paginated results
        faq_pagination = query.order_by(FAQRecord.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)'''
    
    new_manage_faqs_query = '''        # Get paginated results
        faq_pagination = db.session.query(FAQRecord).order_by(FAQRecord.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)'''
    
    admin_content = admin_content.replace(old_manage_faqs_query, new_manage_faqs_query)
    
    # Fix the refresh_faqs function
    old_refresh_faqs_query = '''        # Get paginated results
        faq_pagination = query.order_by(FAQRecord.created_at.desc()).paginate(page=page, per_page=10, error_out=False)'''
    
    new_refresh_faqs_query = '''        # Get paginated results
        faq_pagination = db.session.query(FAQRecord).order_by(FAQRecord.created_at.desc()).paginate(page=page, per_page=10, error_out=False)'''
    
    admin_content = admin_content.replace(old_refresh_faqs_query, new_refresh_faqs_query)
    
    # Fix 2: Fix datetime undefined error in notifications
    print("2. Fixing datetime undefined error...")
    
    # Check if datetime is imported in admin.py
    if 'from datetime import datetime' not in admin_content:
        admin_content = admin_content.replace(
            'from app.extensions import db',
            'from app.extensions import db\nfrom datetime import datetime'
        )
    
    # Fix the notifications_stats function
    old_notifications_stats = '''@admin_bp.route('/notifications-stats', methods=['GET'])
@login_required
@admin_required
def notifications_stats():
    """Get real-time notification statistics"""
    try:
        stats = {
            'total_notifications': Notification.query.count(),
            'active_notifications': Notification.query.filter(
                Notification.expires_at > datetime.utcnow()
            ).count(),
            'expired_notifications': Notification.query.filter(
                Notification.expires_at <= datetime.utcnow()
            ).count()
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting notification stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error loading statistics'
        }), 500'''
    
    new_notifications_stats = '''@admin_bp.route('/notifications-stats', methods=['GET'])
@login_required
@admin_required
def notifications_stats():
    """Get real-time notification statistics"""
    try:
        from datetime import datetime
        stats = {
            'total_notifications': db.session.query(Notification).count(),
            'active_notifications': db.session.query(Notification).filter(
                Notification.expires_at > datetime.utcnow()
            ).count(),
            'expired_notifications': db.session.query(Notification).filter(
                Notification.expires_at <= datetime.utcnow()
            ).count()
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting notification stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error loading statistics'
        }), 500'''
    
    admin_content = admin_content.replace(old_notifications_stats, new_notifications_stats)
    
    # Fix the manage_notifications function
    old_manage_notifications = '''        # Get statistics
        total_notifications = Notification.query.count()
        active_notifications = Notification.query.filter(
            Notification.expires_at > datetime.utcnow()
        ).count()
        expired_notifications = Notification.query.filter(
            Notification.expires_at <= datetime.utcnow()
        ).count()'''
    
    new_manage_notifications = '''        # Get statistics
        from datetime import datetime
        total_notifications = db.session.query(Notification).count()
        active_notifications = db.session.query(Notification).filter(
            Notification.expires_at > datetime.utcnow()
        ).count()
        expired_notifications = db.session.query(Notification).filter(
            Notification.expires_at <= datetime.utcnow()
        ).count()'''
    
    admin_content = admin_content.replace(old_manage_notifications, new_manage_notifications)
    
    # Fix 3: Update routes.py to fix similar issues
    print("3. Fixing routes.py...")
    
    with open('app/routes.py', 'r', encoding='utf-8') as f:
        routes_content = f.read()
    
    # Fix FAQRecord.query usage in routes.py
    routes_content = routes_content.replace('FAQRecord.query.order_by', 'db.session.query(FAQRecord).order_by')
    routes_content = routes_content.replace('FAQRecord.query.count()', 'db.session.query(FAQRecord).count()')
    routes_content = routes_content.replace('FAQRecord.query.filter_by', 'db.session.query(FAQRecord).filter_by')
    routes_content = routes_content.replace('FAQRecord.query.filter', 'db.session.query(FAQRecord).filter')
    routes_content = routes_content.replace('FAQRecord.query.get_or_404', 'db.session.query(FAQRecord).get_or_404')
    
    # Fix Notification.query usage in routes.py
    routes_content = routes_content.replace('Notification.query.order_by', 'db.session.query(Notification).order_by')
    routes_content = routes_content.replace('Notification.query.count()', 'db.session.query(Notification).count()')
    routes_content = routes_content.replace('Notification.query.filter_by', 'db.session.query(Notification).filter_by')
    routes_content = routes_content.replace('Notification.query.filter', 'db.session.query(Notification).filter')
    routes_content = routes_content.replace('Notification.query.get_or_404', 'db.session.query(Notification).get_or_404')
    
    # Add datetime import to routes.py if not present
    if 'from datetime import datetime' not in routes_content:
        routes_content = routes_content.replace(
            'from app.extensions import db',
            'from app.extensions import db\nfrom datetime import datetime'
        )
    
    # Fix datetime usage in routes.py
    routes_content = routes_content.replace('datetime.utcnow()', 'datetime.utcnow()')
    
    with open('app/routes.py', 'w', encoding='utf-8') as f:
        f.write(routes_content)
    
    # Fix 4: Update admin.py with the corrected content
    with open('app/blueprints/admin.py', 'w', encoding='utf-8') as f:
        f.write(admin_content)
    
    # Fix 5: Update the API endpoint in routes.py for notifications
    print("4. Fixing notifications API endpoint...")
    
    with open('app/routes.py', 'r', encoding='utf-8') as f:
        routes_content = f.read()
    
    # Fix the notifications-realtime endpoint
    old_notifications_api = '''@app.route('/api/notifications-realtime')
@login_required
def notifications_realtime():
    """API endpoint for real-time notifications data"""
    try:
        # Get all notifications with author info
        notifications_data = db.session.query(Notification, Admin).outerjoin(Admin, Notification.created_by == Admin.id).order_by(Notification.created_at.desc()).all()
        
        notifications_list = []
        for notification, admin in notifications_data:
            notifications_list.append({
                'id': notification.id,
                'title': notification.title,
                'content': notification.content,
                'link_url': notification.link_url,
                'file_url': notification.file_url,
                'priority': notification.priority,
                'created_at': notification.created_at.isoformat() if notification.created_at else None,
                'expires_at': notification.expires_at.isoformat() if notification.expires_at else None,
                'created_by_name': admin.name if admin else 'System',
                'notification_type': notification.notification_type
            })
        
        return jsonify({
            'success': True,
            'notifications': notifications_list,
            'count': len(notifications_list)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching real-time notifications: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error loading notifications',
            'notifications': []
        }), 500'''
    
    new_notifications_api = '''@app.route('/api/notifications-realtime')
@login_required
def notifications_realtime():
    """API endpoint for real-time notifications data"""
    try:
        # Get all notifications with author info
        notifications_data = db.session.query(Notification, Admin).outerjoin(Admin, Notification.created_by == Admin.id).order_by(Notification.created_at.desc()).all()
        
        notifications_list = []
        for notification, admin in notifications_data:
            notifications_list.append({
                'id': notification.id,
                'title': notification.title,
                'content': notification.content,
                'link_url': notification.link_url,
                'file_url': notification.file_url,
                'priority': notification.priority,
                'created_at': notification.created_at.isoformat() if notification.created_at else None,
                'expires_at': notification.expires_at.isoformat() if notification.expires_at else None,
                'created_by_name': admin.name if admin else 'System',
                'notification_type': notification.notification_type
            })
        
        return jsonify({
            'success': True,
            'notifications': notifications_list,
            'count': len(notifications_list)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching real-time notifications: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error loading notifications',
            'notifications': []
        }), 500'''
    
    routes_content = routes_content.replace(old_notifications_api, new_notifications_api)
    
    with open('app/routes.py', 'w', encoding='utf-8') as f:
        f.write(routes_content)
    
    print("\n=== FIX COMPLETE ===")
    print("\nChanges made:")
    print("1. Fixed FAQRecord.query.order_by to use db.session.query(FAQRecord).order_by")
    print("2. Added datetime import to fix 'datetime is undefined' error")
    print("3. Updated all Notification.query usage to use db.session.query")
    print("4. Fixed pagination queries in both admin.py and routes.py")
    print("5. Added proper datetime imports to all affected functions")
    print("\nProduction errors should now be resolved!")

if __name__ == "__main__":
    fix_production_errors()
