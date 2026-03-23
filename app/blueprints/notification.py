from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from app.extensions import db
from app.models import Student, Faculty, Notification, Complaint, Result
from app.services.safe_execute import safe_execute
from datetime import datetime
import json

notification_bp = Blueprint('notification', __name__, url_prefix='/notification')

def notification_required(f):
    """Decorator to ensure user has notification privileges (admin, faculty, accounts)"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            # Check if user has any of the allowed roles
            if hasattr(current_user, 'role'):
                user_role = current_user.role
            elif hasattr(current_user, 'user_role'):
                user_role = current_user.user_role
            else:
                user_role = 'student'
            
            if user_role not in ['admin', 'faculty', 'accounts']:
                flash('Access denied. Notification privileges required.', 'error')
                return redirect(url_for('auth.login'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator(f)

@notification_bp.route('/send-notification', methods=['GET', 'POST'])
@login_required
@notification_required
def send_notification():
    """Send notification - shared across all roles"""
    # Check if this is an AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if request.method == 'POST':
        try:
            from datetime import datetime, timedelta
            
            # Get form data
            title = request.form.get('title')
            content = request.form.get('content')
            link_url = request.form.get('link_url')
            file_url = request.form.get('file_url')
            expiry_days = int(request.form.get('expiry_days') or current_app.config.get('NOTIFICATION_EXPIRY_DAYS', 4))
            
            # Validate required fields
            if not title or not content:
                error_msg = 'Title and content are required fields.'
                if is_ajax:
                    return jsonify({
                        'success': False,
                        'message': error_msg
                    })
                else:
                    flash(error_msg, 'error')
                    return render_template('faculty_send_notification.html')
            
            notification = Notification(
                title=title,
                content=content,
                link_url=link_url,
                file_url=file_url,
                notification_type=request.form.get('notification_type', 'general'),
                priority=request.form.get('priority', 'medium'),
                expires_at=datetime.utcnow() + timedelta(days=expiry_days),
                created_by=current_user.id
            )
            
            db.session.add(notification)
            db.session.commit()
            
            # Trigger real-time update for connected clients
            try:
                current_app.config['LAST_NOTIFICATION_ID'] = notification.id
                current_app.logger.info(f"Triggered real-time update for notification {notification.id}")
            except Exception as e:
                current_app.logger.warning(f"Could not trigger real-time update: {e}")
            
            success_msg = '✅ Notification sent successfully!'
            if is_ajax:
                return jsonify({
                    'success': True,
                    'message': success_msg,
                    'notification': {
                        'id': notification.id,
                        'title': notification.title,
                        'content': notification.content,
                        'link_url': notification.link_url,
                        'file_url': notification.file_url,
                        'notification_type': notification.notification_type,
                        'priority': notification.priority,
                        'expires_at': notification.expires_at.strftime('%Y-%m-%d %H:%M') if notification.expires_at else 'N/A',
                        'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M') if notification.created_at else 'N/A'
                    }
                })
            else:
                flash(success_msg, 'success')
                # Redirect based on user role
                if hasattr(current_user, 'role'):
                    user_role = current_user.role
                elif hasattr(current_user, 'user_role'):
                    user_role = current_user.user_role
                else:
                    user_role = 'faculty'
                
                if user_role == 'admin':
                    return redirect(url_for('admin.admin_dashboard_main'))
                elif user_role == 'accounts':
                    return redirect(url_for('accounts.accounts_dashboard'))
                else:
                    return redirect(url_for('faculty.faculty_dashboard'))
            
        except Exception as e:
            current_app.logger.error(f"Error sending notification from {current_user.id}: {str(e)}")
            db.session.rollback()
            
            error_msg = f'❌ Error sending notification: {str(e)}'
            if is_ajax:
                return jsonify({
                    'success': False,
                    'message': error_msg
                })
            else:
                flash(error_msg, 'error')
    
    return render_template('faculty_send_notification.html')

@notification_bp.route('/edit-notification/<int:notification_id>', methods=['GET', 'POST'])
@login_required
@notification_required
def edit_notification(notification_id):
    """Edit notification - shared across all roles"""
    try:
        notification = Notification.query.get_or_404(notification_id)
        
        if request.method == 'POST':
            try:
                from datetime import datetime, timedelta
                
                # Get form data
                notification.title = request.form.get('title')
                notification.content = request.form.get('content')
                notification.link_url = request.form.get('link_url')
                notification.file_url = request.form.get('file_url')
                notification.notification_type = request.form.get('notification_type', 'general')
                notification.priority = request.form.get('priority', 'medium')
                
                # Update expiry if changed
                expiry_days = int(request.form.get('expiry_days') or 4)
                notification.expires_at = datetime.utcnow() + timedelta(days=expiry_days)
                
                db.session.commit()
                flash('✅ Notification updated successfully!', 'success')
                
                # Redirect based on user role
                if hasattr(current_user, 'role'):
                    user_role = current_user.role
                elif hasattr(current_user, 'user_role'):
                    user_role = current_user.user_role
                else:
                    user_role = 'faculty'
                
                if user_role == 'admin':
                    return redirect(url_for('admin.view_notifications'))
                elif user_role == 'accounts':
                    return redirect(url_for('notification.manage_notifications'))
                else:
                    return redirect(url_for('faculty.manage_notifications'))
                
            except Exception as e:
                current_app.logger.error(f"Error updating notification: {str(e)}")
                flash(f'❌ Error updating notification: {str(e)}', 'error')
        
        return render_template('faculty_edit_notification.html', notification=notification)
        
    except Exception as e:
        current_app.logger.error(f"Error loading edit notification: {str(e)}")
        flash('Error loading notification.', 'error')
        return redirect(url_for('notification.manage_notifications'))

@notification_bp.route('/delete-notification/<int:notification_id>', methods=['POST'])
@login_required
@notification_required
def delete_notification(notification_id):
    """Delete notification - shared across all roles"""
    try:
        notification = Notification.query.get_or_404(notification_id)
        
        db.session.delete(notification)
        db.session.commit()
        flash('✅ Notification deleted successfully!', 'success')
        
    except Exception as e:
        current_app.logger.error(f"Error deleting notification: {str(e)}")
        flash(f'❌ Error deleting notification: {str(e)}', 'error')
    
    # Redirect based on user role
    if hasattr(current_user, 'role'):
        user_role = current_user.role
    elif hasattr(current_user, 'user_role'):
        user_role = current_user.user_role
    else:
        user_role = 'faculty'
    
    if user_role == 'admin':
        return redirect(url_for('admin.view_notifications'))
    elif user_role == 'accounts':
        return redirect(url_for('notification.manage_notifications'))
    else:
        return redirect(url_for('faculty.manage_notifications'))

@notification_bp.route('/manage-notifications')
@login_required
@notification_required
def manage_notifications():
    """Manage notifications - shared across all roles"""
    try:
        # Get all notifications, newest first
        notifications = Notification.query.order_by(Notification.created_at.desc()).all()
        return render_template('faculty_manage_notifications.html', notifications=notifications)
    except Exception as e:
        current_app.logger.error(f"Error loading manage notifications: {str(e)}")
        flash('Error loading notifications.', 'error')
        return render_template('faculty_manage_notifications.html', notifications=[])
