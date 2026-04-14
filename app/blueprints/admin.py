"""
Admin Blueprint - Administrative Routes
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.extensions import db
from app.models import (
    Admin, Student, Faculty, Notification, Result, 
    FeeRecord, Complaint, ChatbotQA, FAQRecord
)
from app.services.analytics_service import AnalyticsService
from app.services.weekly_report_service import WeeklyReportService
from app.services.email_service import EmailService
from app.config import Config
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator to require admin privileges"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if user has admin role (supports both Admin and Faculty tables)
        user_role = getattr(current_user, 'role', None) or getattr(current_user, 'user_role', None)
        if user_role != 'admin':
            return jsonify({'error': 'Admin privileges required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard with analytics"""
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('auth.login'))
    
    try:
        # Get analytics data
        analytics = AnalyticsService.get_dashboard_analytics()
        
        return render_template('admin/dashboard.html', 
                           analytics=analytics,
                           user=current_user)
    except Exception as e:
        current_app.logger.error(f"Error loading admin dashboard: {str(e)}")
        flash('Error loading dashboard. Please try again.', 'error')
        return render_template('admin/dashboard.html', 
                           analytics={'total_queries': 0, 'unknown_queries': 0},
                           user=current_user)


@admin_bp.route('/analytics')
@login_required
@admin_required
def get_analytics():
    """Get analytics data for dashboard"""
    try:
        # Get time period from request
        period = request.args.get('period', '7days')
        
        # Get analytics data
        analytics = AnalyticsService.get_analytics_data(period)
        
        return jsonify({
            'success': True,
            'data': analytics
        })
    except Exception as e:
        current_app.logger.error(f"Error getting analytics: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/students')
@login_required
@admin_required
def manage_students():
    """Manage students"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        search = request.args.get('search', '')
        
        # Build query
        query = Student.query
        
        if search:
            query = query.filter(
                Student.roll_number.ilike(f'%{search}%') |
                Student.name.ilike(f'%{search}%') |
                Student.email.ilike(f'%{search}%')
            )
        
        # Paginate
        students = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('admin/students.html', 
                           students=students,
                           search=search,
                           user=current_user)
    except Exception as e:
        current_app.logger.error(f"Error loading students: {str(e)}")
        flash('Error loading students. Please try again.', 'error')
        return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/faculty')
@login_required
@admin_required
def manage_faculty():
    """Manage faculty"""
    try:
        faculty = Faculty.query.all()
        return render_template('admin/faculty.html', 
                           faculty=faculty,
                           user=current_user)
    except Exception as e:
        current_app.logger.error(f"Error loading faculty: {str(e)}")
        flash('Error loading faculty. Please try again.', 'error')
        return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/notifications')
@login_required
@admin_required
def manage_notifications():
    """Manage notifications"""
    try:
        notifications = Notification.query.order_by(
            Notification.created_at.desc()
        ).all()
        
        return render_template('admin/notifications.html', 
                           notifications=notifications,
                           user=current_user)
    except Exception as e:
        current_app.logger.error(f"Error loading notifications: {str(e)}")
        flash('Error loading notifications. Please try again.', 'error')
        return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/create-notification', methods=['GET', 'POST'])
@login_required
@admin_required
def create_notification():
    """Create new notification"""
    if request.method == 'GET':
        return render_template('admin/create_notification.html', user=current_user)
    
    try:
        # Get form data
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        priority = request.form.get('priority', 'medium')
        expires_days = request.form.get('expires_days', 7, type=int)
        
        # Validate
        if not title or not content:
            flash('Title and content are required.', 'error')
            return render_template('admin/create_notification.html', user=current_user)
        
        # Create notification
        notification = Notification(
            title=title,
            content=content,
            priority=priority,
            expires_at=datetime.utcnow() + timedelta(days=expires_days),
            created_by=current_user.id
        )
        
        db.session.add(notification)
        db.session.commit()
        
        flash('Notification created successfully.', 'success')
        return redirect(url_for('admin.manage_notifications'))
        
    except Exception as e:
        current_app.logger.error(f"Error creating notification: {str(e)}")
        flash('Error creating notification. Please try again.', 'error')
        return render_template('admin/create_notification.html', user=current_user)


@admin_bp.route('/delete-notification/<int:notification_id>', methods=['POST'])
@login_required
@admin_required
def delete_notification(notification_id):
    """Delete notification"""
    try:
        notification = Notification.query.get_or_404(notification_id)
        db.session.delete(notification)
        db.session.commit()
        
        flash('Notification deleted successfully.', 'success')
        return redirect(url_for('admin.manage_notifications'))
        
    except Exception as e:
        current_app.logger.error(f"Error deleting notification: {str(e)}")
        flash('Error deleting notification. Please try again.', 'error')
        return redirect(url_for('admin.manage_notifications'))


@admin_bp.route('/complaints')
@login_required
@admin_required
def manage_complaints():
    """Manage complaints"""
    try:
        complaints = Complaint.query.order_by(
            Complaint.created_at.desc()
        ).all()
        
        return render_template('admin/complaints.html', 
                           complaints=complaints,
                           user=current_user)
    except Exception as e:
        current_app.logger.error(f"Error loading complaints: {str(e)}")
        flash('Error loading complaints. Please try again.', 'error')
        return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/resolve-complaint/<int:complaint_id>', methods=['POST'])
@login_required
@admin_required
def resolve_complaint(complaint_id):
    """Resolve complaint"""
    try:
        complaint = Complaint.query.get_or_404(complaint_id)
        complaint.status = 'resolved'
        complaint.resolved_at = datetime.utcnow()
        complaint.resolved_by = current_user.id
        
        db.session.commit()
        
        flash('Complaint resolved successfully.', 'success')
        return redirect(url_for('admin.manage_complaints'))
        
    except Exception as e:
        current_app.logger.error(f"Error resolving complaint: {str(e)}")
        flash('Error resolving complaint. Please try again.', 'error')
        return redirect(url_for('admin.manage_complaints'))


def format_time_ago(timestamp):
    """Format timestamp as 'X time ago'"""
    if not timestamp:
        return 'Never'
    
    now = datetime.utcnow()
    diff = now - timestamp
    
    if diff < timedelta(minutes=1):
        return 'Just now'
    elif diff < timedelta(hours=1):
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff < timedelta(days=1):
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = diff.days
        return f"{days} day{'s' if days != 1 else ''} ago"


# Weekly Report Route
@admin_bp.route('/send-weekly-report', methods=['POST'])
@login_required
@admin_required
def send_weekly_report():
    """Generate and send weekly report"""
    try:
        from app.services.weekly_report_service import WeeklyReportService
        from app.services.email_service import EmailService
        from app.config import Config
        import os
        
        # Generate weekly report
        csv_path = WeeklyReportService.generate_weekly_report()
        
        if csv_path and os.path.exists(csv_path):
            # Get file info
            file_name = os.path.basename(csv_path)
            
            # Weekly report is already sent by the background service
            # No need to send again, just return
            
            return jsonify({
                'success': True,
                'message': f'Weekly report generated and sent to {Config.ADMIN_EMAIL}',
                'file_path': csv_path,
                'file_name': file_name
            })
            
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to generate weekly report file'
            })
            
    except Exception as e:
        current_app.logger.error(f"Error in send_weekly_report: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error generating weekly report: {str(e)}'
        }), 500
