"""
Admin Blueprint - Administrative Routes
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.extensions import db
from app.models import (
    Admin, Student, Faculty, Notification, Result, 
    FeeRecord, Complaint, ChatbotQA, FAQRecord, PredefinedInfo, FAQ
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
        
        # Add additional metrics for dashboard
        analytics['total_students'] = Student.query.count() if Student else 0
        analytics['total_faculty'] = Faculty.query.count() if Faculty else 0
        analytics['active_notifications'] = Notification.query.count() if Notification else 0
        analytics['pending_complaints'] = Complaint.query.filter_by(status='pending').count() if Complaint else 0
        
        return render_template('admin_dashboard_edubot.html', 
                           total_students=analytics.get('total_students', 0),
                           total_faculty=analytics.get('total_faculty', 0),
                           total_notifications=analytics.get('active_notifications', 0),
                           user=current_user)
    except Exception as e:
        current_app.logger.error(f"Error loading admin dashboard: {str(e)}")
        flash('Error loading dashboard. Please try again.', 'error')
        return render_template('admin_dashboard_edubot.html', 
                           total_students=0,
                           total_faculty=0,
                           total_notifications=0,
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
        
        return render_template('students.html', 
                           students=students,
                           search=search,
                           user=current_user)
    except Exception as e:
        current_app.logger.error(f"Error loading students: {str(e)}")
        flash('Error loading students. Please try again.', 'error')
        return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/fee-records')
@login_required
@admin_required
def manage_fee_records():
    """Manage fee records (read-only)"""
    try:
        fee_records = FeeRecord.query.order_by(
            FeeRecord.last_updated.desc()
        ).all()
        
        return render_template('admin/fee_records.html', 
                           fee_records=fee_records,
                           read_only=True,
                           user=current_user)
    except Exception as e:
        current_app.logger.error(f"Error loading fee records: {str(e)}")
        flash('Error loading fee records. Please try again.', 'error')
        return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/faculty')
@login_required
@admin_required
def manage_faculty():
    """Manage faculty"""
    try:
        faculty = Faculty.query.all()
        return render_template('faculty.html', 
                           faculty=faculty,
                           user=current_user,
                           can_create=True,
                           can_edit=False)
    except Exception as e:
        current_app.logger.error(f"Error loading faculty: {str(e)}")
        flash('Error loading faculty. Please try again.', 'error')
        return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/create-faculty', methods=['GET', 'POST'])
@login_required
@admin_required
def create_faculty():
    """Create new faculty"""
    if request.method == 'GET':
        return render_template('admin/create_faculty.html', user=current_user)
    
    try:
        # Get form data
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        department = request.form.get('department', '').strip()
        phone = request.form.get('phone', '').strip()
        consultation_time = request.form.get('consultation_time', '').strip()
        
        # Validate
        if not name or not email:
            flash('Name and email are required.', 'error')
            return render_template('admin/create_faculty.html', user=current_user)
        
        # Create faculty
        faculty = Faculty(
            name=name,
            email=email,
            department=department,
            phone=phone,
            consultation_time=consultation_time,
            role='faculty'
        )
        
        db.session.add(faculty)
        db.session.commit()
        
        flash('Faculty created successfully.', 'success')
        return redirect(url_for('admin.manage_faculty'))
        
    except Exception as e:
        current_app.logger.error(f"Error creating faculty: {str(e)}")
        flash('Error creating faculty. Please try again.', 'error')
        return render_template('admin/create_faculty.html', user=current_user)


@admin_bp.route('/delete-faculty/<int:faculty_id>', methods=['POST'])
@login_required
@admin_required
def delete_faculty(faculty_id):
    """Delete faculty"""
    try:
        faculty = Faculty.query.get_or_404(faculty_id)
        db.session.delete(faculty)
        db.session.commit()
        
        flash('Faculty deleted successfully.', 'success')
        return redirect(url_for('admin.manage_faculty'))
        
    except Exception as e:
        current_app.logger.error(f"Error deleting faculty: {str(e)}")
        flash('Error deleting faculty. Please try again.', 'error')
        return redirect(url_for('admin.manage_faculty'))


@admin_bp.route('/notifications')
@login_required
@admin_required
def manage_notifications():
    """Manage notifications"""
    try:
        notifications = Notification.query.order_by(
            Notification.created_at.desc()
        ).all()
        
        return render_template('notifications.html', 
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
        return render_template('create_notification.html', user=current_user)
    
    try:
        # Get form data
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        priority = request.form.get('priority', 'medium')
        expires_days = request.form.get('expires_days', 7, type=int)
        
        # Validate
        if not title or not content:
            flash('Title and content are required.', 'error')
            return render_template('create_notification.html', user=current_user)
        
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
        return render_template('create_notification.html', user=current_user)


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
        
        return render_template('manage_complaints.html', 
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


# Predefined Info Routes
@admin_bp.route('/predefined-info')
@login_required
@admin_required
def manage_predefined_info():
    """Manage predefined information"""
    try:
        predefined_info = PredefinedInfo.query.order_by(
            PredefinedInfo.section, PredefinedInfo.title
        ).all()
        
        return render_template('manage_predefined_info.html', 
                           predefined_info=predefined_info,
                           user=current_user)
    except Exception as e:
        current_app.logger.error(f"Error loading predefined info: {str(e)}")
        flash('Error loading predefined info. Please try again.', 'error')
        return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/add-predefined-info', methods=['GET', 'POST'])
@login_required
@admin_required
def add_predefined_info():
    """Add new predefined information"""
    if request.method == 'GET':
        return render_template('add_predefined_info.html', user=current_user)
    
    try:
        # Get form data
        section = request.form.get('section', '').strip()
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        category = request.form.get('category', '').strip()
        
        # Validate
        if not section or not title or not content:
            flash('Section, title, and content are required.', 'error')
            return render_template('add_predefined_info.html', user=current_user)
        
        # Create predefined info
        predefined_info = PredefinedInfo(
            section=section,
            title=title,
            content=content,
            category=category,
            updated_by=current_user.id
        )
        
        db.session.add(predefined_info)
        db.session.commit()
        
        flash('Predefined information added successfully.', 'success')
        return redirect(url_for('admin.manage_predefined_info'))
        
    except Exception as e:
        current_app.logger.error(f"Error adding predefined info: {str(e)}")
        flash('Error adding predefined information. Please try again.', 'error')
        return render_template('add_predefined_info.html', user=current_user)


@admin_bp.route('/edit-predefined-info/<int:info_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_predefined_info(info_id):
    """Edit predefined information"""
    predefined_info = PredefinedInfo.query.get_or_404(info_id)
    
    if request.method == 'GET':
        return render_template('edit_predefined_info.html', 
                           predefined_info=predefined_info,
                           user=current_user)
    
    try:
        # Get form data
        section = request.form.get('section', '').strip()
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        category = request.form.get('category', '').strip()
        
        # Validate
        if not section or not title or not content:
            flash('Section, title, and content are required.', 'error')
            return render_template('edit_predefined_info.html', 
                               predefined_info=predefined_info,
                               user=current_user)
        
        # Update predefined info
        predefined_info.section = section
        predefined_info.title = title
        predefined_info.content = content
        predefined_info.category = category
        predefined_info.updated_by = current_user.id
        predefined_info.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Predefined information updated successfully.', 'success')
        return redirect(url_for('admin.manage_predefined_info'))
        
    except Exception as e:
        current_app.logger.error(f"Error updating predefined info: {str(e)}")
        flash('Error updating predefined information. Please try again.', 'error')
        return render_template('edit_predefined_info.html', 
                           predefined_info=predefined_info,
                           user=current_user)


@admin_bp.route('/delete-predefined-info/<int:info_id>', methods=['POST'])
@login_required
@admin_required
def delete_predefined_info(info_id):
    """Delete predefined information"""
    try:
        predefined_info = PredefinedInfo.query.get_or_404(info_id)
        db.session.delete(predefined_info)
        db.session.commit()
        
        flash('Predefined information deleted successfully.', 'success')
        return redirect(url_for('admin.manage_predefined_info'))
        
    except Exception as e:
        current_app.logger.error(f"Error deleting predefined info: {str(e)}")
        flash('Error deleting predefined information. Please try again.', 'error')
        return redirect(url_for('admin.manage_predefined_info'))


# FAQ Management Routes
@admin_bp.route('/faqs')
@login_required
@admin_required
def manage_faqs():
    """Manage frequently asked questions"""
    try:
        faqs = FAQ.query.order_by(
            FAQ.priority.desc(), FAQ.created_at.desc()
        ).all()
        
        return render_template('manage_faqs.html', 
                           faqs=faqs,
                           user=current_user)
    except Exception as e:
        current_app.logger.error(f"Error loading FAQs: {str(e)}")
        flash('Error loading FAQs. Please try again.', 'error')
        return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/add-faq', methods=['GET', 'POST'])
@login_required
@admin_required
def add_faq():
    """Add new FAQ"""
    if request.method == 'GET':
        return render_template('add_faq.html', user=current_user)
    
    try:
        # Get form data
        question = request.form.get('question', '').strip()
        answer = request.form.get('answer', '').strip()
        category = request.form.get('category', '').strip()
        priority = request.form.get('priority', 1, type=int)
        
        # Validate
        if not question or not answer:
            flash('Question and answer are required.', 'error')
            return render_template('add_faq.html', user=current_user)
        
        # Create FAQ
        faq = FAQ(
            question=question,
            answer=answer,
            category=category,
            priority=priority,
            updated_by=current_user.id
        )
        
        db.session.add(faq)
        db.session.commit()
        
        flash('FAQ added successfully.', 'success')
        return redirect(url_for('admin.manage_faqs'))
        
    except Exception as e:
        current_app.logger.error(f"Error adding FAQ: {str(e)}")
        flash('Error adding FAQ. Please try again.', 'error')
        return render_template('add_faq.html', user=current_user)


@admin_bp.route('/edit-faq/<int:faq_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_faq(faq_id):
    """Edit FAQ"""
    faq = FAQ.query.get_or_404(faq_id)
    
    if request.method == 'GET':
        return render_template('edit_faq.html', 
                           faq=faq,
                           user=current_user)
    
    try:
        # Get form data
        question = request.form.get('question', '').strip()
        answer = request.form.get('answer', '').strip()
        category = request.form.get('category', '').strip()
        priority = request.form.get('priority', 1, type=int)
        
        # Validate
        if not question or not answer:
            flash('Question and answer are required.', 'error')
            return render_template('edit_faq.html', 
                               faq=faq,
                               user=current_user)
        
        # Update FAQ
        faq.question = question
        faq.answer = answer
        faq.category = category
        faq.priority = priority
        faq.updated_by = current_user.id
        faq.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('FAQ updated successfully.', 'success')
        return redirect(url_for('admin.manage_faqs'))
        
    except Exception as e:
        current_app.logger.error(f"Error updating FAQ: {str(e)}")
        flash('Error updating FAQ. Please try again.', 'error')
        return render_template('edit_faq.html', 
                           faq=faq,
                           user=current_user)


@admin_bp.route('/delete-faq/<int:faq_id>', methods=['POST'])
@login_required
@admin_required
def delete_faq(faq_id):
    """Delete FAQ"""
    try:
        faq = FAQ.query.get_or_404(faq_id)
        db.session.delete(faq)
        db.session.commit()
        
        flash('FAQ deleted successfully.', 'success')
        return redirect(url_for('admin.manage_faqs'))
        
    except Exception as e:
        current_app.logger.error(f"Error deleting FAQ: {str(e)}")
        flash('Error deleting FAQ. Please try again.', 'error')
        return redirect(url_for('admin.manage_faqs'))
