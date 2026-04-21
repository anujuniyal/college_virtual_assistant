from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from app.extensions import db
from app.models import Student, Faculty, Notification, Complaint, Result
from app.services.safe_execute import safe_execute
from datetime import datetime
import json

faculty_bp = Blueprint('faculty', __name__, url_prefix='/faculty')

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

def faculty_required(f):
    """Decorator to ensure user has faculty privileges"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            # Check if user has faculty or admin privileges
            if hasattr(current_user, 'role'):
                user_role = current_user.role
            elif hasattr(current_user, 'user_role'):
                user_role = current_user.user_role
            else:
                user_role = 'faculty'  # Default to faculty
            
            if user_role not in ['faculty', 'admin']:
                flash('Access denied. Faculty privileges required.', 'error')
                return redirect(url_for('auth.login'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator(f)

@faculty_bp.route('/dashboard')
@login_required
@faculty_required
def faculty_dashboard():
    """Enhanced faculty dashboard with admin-like features"""
    try:
        # Get comprehensive statistics like admin
        total_students = safe_execute(lambda: Student.query.count()) or 0
        total_notifications = safe_execute(
            lambda: Notification.query.filter(
                Notification.expires_at > datetime.utcnow()
            ).count()
        ) or 0
        total_complaints = safe_execute(lambda: Complaint.query.count()) or 0
        pending_complaints = safe_execute(
            lambda: Complaint.query.filter_by(status='pending').count()
        ) or 0
        total_results = safe_execute(lambda: Result.query.count()) or 0
        
        # Get faculty-specific info
        faculty_info = safe_execute(
            lambda: Faculty.query.filter_by(email=current_user.email).first()
        )
        
        # Create faculty_info dict if not found
        if not faculty_info:
            faculty_info = {
                'name': current_user.username,
                'email': current_user.email,
                'department': 'Computer Science',
                'phone': 'Not specified',
                'consultation_time': 'Not specified'
            }
        
        # Get recent notifications
        recent_notifications = safe_execute(
            lambda: Notification.query.order_by(Notification.created_at.desc()).limit(5).all()
        ) or []
        
        return render_template('faculty_dashboard_edubot.html',
                             faculty_info=faculty_info,
                             total_students=total_students,
                             total_notifications=total_notifications,
                             total_complaints=total_complaints,
                             pending_complaints=pending_complaints,
                             total_results=total_results,
                             recent_notifications=recent_notifications)
    
    except Exception as e:
        current_app.logger.error(f"Faculty dashboard error: {str(e)}")
        flash('Error loading faculty dashboard.', 'error')
        return render_template('faculty_dashboard_edubot.html',
                             faculty_info={
                                 'name': current_user.username,
                                 'email': current_user.email,
                                 'department': 'Computer Science',
                                 'phone': 'Not specified',
                                 'consultation_time': 'Not specified'
                             },
                             total_students=0,
                             total_notifications=0,
                             total_complaints=0,
                             pending_complaints=0,
                             total_results=0,
                             recent_notifications=[])

@faculty_bp.route('/send-notification', methods=['GET', 'POST'])
@login_required
@notification_required
def send_notification():
    """Enhanced send notification to students"""
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
            
            # Get the correct admin ID for created_by field
            admin_id = None
            if hasattr(current_user, 'role') and current_user.role == 'admin':
                # Current user is from Admin table
                admin_id = current_user.id
            elif hasattr(current_user, 'user_role') and current_user.user_role == 'admin':
                # Current user is from Admin table (alternative check)
                admin_id = current_user.id
            else:
                # Current user is faculty, find or create corresponding admin entry
                from app.models import Admin
                admin_entry = Admin.query.filter_by(email=current_user.email).first()
                if admin_entry:
                    admin_id = admin_entry.id
                else:
                    # Create admin entry for faculty user
                    admin_entry = Admin(
                        username=current_user.email.split('@')[0],
                        email=current_user.email,
                        role='faculty',
                        password_hash=current_user.password_hash if hasattr(current_user, 'password_hash') else ''
                    )
                    db.session.add(admin_entry)
                    db.session.commit()
                    admin_id = admin_entry.id
            
            notification = Notification(
                title=title,
                content=content,
                link_url=link_url,
                file_url=file_url,
                notification_type=request.form.get('notification_type', 'general'),
                priority=request.form.get('priority', 'medium'),
                expires_at=datetime.utcnow() + timedelta(days=expiry_days),
                created_by=admin_id
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
                return redirect(url_for('faculty.faculty_dashboard'))
            
        except Exception as e:
            db.session.rollback()  # Rollback session to prevent PendingRollbackError
            current_app.logger.error(f"Error sending notification from faculty: {str(e)}")
            
            error_msg = f'❌ Error sending notification: {str(e)}'
            if is_ajax:
                return jsonify({
                    'success': False,
                    'message': error_msg
                })
            else:
                flash(error_msg, 'error')
    
    return render_template('faculty_send_notification.html')

@faculty_bp.route('/edit-notification/<int:notification_id>', methods=['GET', 'POST'])
@login_required
@notification_required
def edit_notification(notification_id):
    """Edit notification"""
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
                return redirect(url_for('faculty.manage_notifications'))
                
            except Exception as e:
                current_app.logger.error(f"Error updating notification: {str(e)}")
                flash(f'❌ Error updating notification: {str(e)}', 'error')
        
        return render_template('faculty_edit_notification.html', notification=notification)
        
    except Exception as e:
        current_app.logger.error(f"Error loading edit notification: {str(e)}")
        flash('Error loading notification.', 'error')
        return redirect(url_for('faculty.manage_notifications'))

@faculty_bp.route('/delete-notification/<int:notification_id>', methods=['POST'])
@login_required
@notification_required
def delete_notification(notification_id):
    """Delete notification"""
    try:
        notification = Notification.query.get_or_404(notification_id)
        
        db.session.delete(notification)
        db.session.commit()
        flash('✅ Notification deleted successfully!', 'success')
        
    except Exception as e:
        current_app.logger.error(f"Error deleting notification: {str(e)}")
        flash(f'❌ Error deleting notification: {str(e)}', 'error')
    
    return redirect(url_for('faculty.manage_notifications'))

@faculty_bp.route('/manage-notifications')
@login_required
@notification_required
def manage_notifications():
    """Manage notifications with edit/delete functionality"""
    try:
        # Get all notifications, newest first
        notifications = Notification.query.order_by(Notification.created_at.desc()).all()
        return render_template('faculty_manage_notifications.html', notifications=notifications)
    except Exception as e:
        current_app.logger.error(f"Error loading manage notifications: {str(e)}")
        flash('Error loading notifications.', 'error')
        return render_template('faculty_manage_notifications.html', notifications=[])

@faculty_bp.route('/dashboard-data')
@faculty_required
def faculty_dashboard_data():
    """AJAX endpoint for faculty dashboard data refresh"""
    try:
        # Get fresh statistics
        total_students = safe_execute(lambda: Student.query.count()) or 0
        total_notifications = safe_execute(
            lambda: Notification.query.filter(
                Notification.expires_at > datetime.utcnow()
            ).count()
        ) or 0
        total_complaints = safe_execute(lambda: Complaint.query.count()) or 0
        pending_complaints = safe_execute(
            lambda: Complaint.query.filter_by(status='pending').count()
        ) or 0
        total_results = safe_execute(lambda: Result.query.count()) or 0
        
        # Get recent notifications
        recent_notifications = safe_execute(
            lambda: Notification.query.order_by(Notification.created_at.desc()).limit(5).all()
        ) or []
        
        # Format recent notifications for JSON response
        recent_notifications_data = []
        for notif in recent_notifications:
            recent_notifications_data.append({
                'id': notif.id,
                'title': notif.title,
                'content': notif.content[:100] + ('...' if len(notif.content) > 100 else ''),
                'created_at': notif.created_at.strftime('%d %b %Y, %I:%M %p') if notif.created_at else 'N/A'
            })
        
        return jsonify({
            'success': True,
            'total_students': total_students,
            'total_notifications': total_notifications,
            'total_complaints': total_complaints,
            'pending_complaints': pending_complaints,
            'total_results': total_results,
            'recent_notifications': recent_notifications_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Faculty dashboard data AJAX error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error loading dashboard data'
        }), 500

@faculty_bp.route('/faculty-manage-students')
@faculty_required
def faculty_manage_students():
    """Manage students with faculty privileges"""
    try:
        students = safe_execute(
            lambda: Student.query.order_by(Student.name).all()
        ) or []
        return render_template('faculty_manage_students.html', students=students)
    except Exception as e:
        current_app.logger.error(f"Error loading faculty manage students: {str(e)}")
        flash('Error loading students.', 'error')
        return render_template('faculty_manage_students.html', students=[])

@faculty_bp.route('/manage-complaints')
@faculty_required
def manage_complaints():
    """Manage complaints with faculty privileges"""
    try:
        complaints = safe_execute(
            lambda: Complaint.query.order_by(Complaint.created_at.desc()).all()
        ) or []
        return render_template('faculty_manage_complaints.html', complaints=complaints)
    except Exception as e:
        current_app.logger.error(f"Error loading faculty manage complaints: {str(e)}")
        flash('Error loading complaints.', 'error')
        return render_template('faculty_manage_complaints.html', complaints=[])

@faculty_bp.route('/manage-results')
@faculty_required
def manage_results():
    """Manage results with faculty privileges"""
    try:
        results = safe_execute(
            lambda: Result.query.order_by(Result.declared_at.desc()).all()
        ) or []
        students = safe_execute(
            lambda: Student.query.order_by(Student.name).all()
        ) or []
        return render_template('faculty_manage_results.html', results=results, students=students)
    except Exception as e:
        current_app.logger.error(f"Error loading faculty manage results: {str(e)}")
        flash('Error loading results.', 'error')
        return render_template('faculty_manage_results.html', results=[], students=[])

@faculty_bp.route('/add-result', methods=['GET', 'POST'])
@faculty_required
def add_result():
    """Add result with faculty privileges"""
    if request.method == 'POST':
        try:
            semester = int(request.form.get('semester') or 1)
            
            # Get the correct admin ID for created_by field
            admin_id = None
            if hasattr(current_user, 'role') and current_user.role == 'admin':
                # Current user is from Admin table
                admin_id = current_user.id
            elif hasattr(current_user, 'user_role') and current_user.user_role == 'admin':
                # Current user is from Admin table (alternative check)
                admin_id = current_user.id
            else:
                # Current user is faculty, find or create corresponding admin entry
                from app.models import Admin
                admin_entry = Admin.query.filter_by(email=current_user.email).first()
                if admin_entry:
                    admin_id = admin_entry.id
                else:
                    # Create admin entry for faculty user
                    admin_entry = Admin(
                        username=current_user.email.split('@')[0],
                        email=current_user.email,
                        role='faculty',
                        password_hash=current_user.password_hash if hasattr(current_user, 'password_hash') else ''
                    )
                    db.session.add(admin_entry)
                    db.session.commit()
                    admin_id = admin_entry.id
            
            result = Result(
                student_id=int(request.form.get('student_id')),
                subject=request.form.get('subject'),
                marks=float(request.form.get('marks')),
                grade=request.form.get('grade'),
                semester=semester,
                created_by=admin_id,
                declared_at=datetime.utcnow(),
            )
            db.session.add(result)
            db.session.commit()
            flash('✅ Result added successfully!', 'success')
            return redirect(url_for('faculty.manage_results'))
        except Exception as e:
            db.session.rollback()  # Rollback session to prevent PendingRollbackError
            current_app.logger.error(f"Error adding result: {str(e)}")
            flash(f'❌ Error adding result: {str(e)}', 'error')
    
    try:
        students = Student.query.order_by(Student.name).all()
    except Exception as e:
        db.session.rollback()  # Rollback if student query fails
        current_app.logger.error(f"Error loading students: {str(e)}")
        students = []
    
    return render_template('faculty_add_result.html', students=students)

@faculty_bp.route('/faculty-profile', methods=['GET', 'POST'])
@faculty_required
def faculty_profile():
    """View/edit faculty profile"""
    try:
        faculty_info = Faculty.query.filter_by(email=current_user.email).first()
        if not faculty_info:
            # Create faculty record if not exists
            faculty_info = Faculty(
                name=current_user.username,
                email=current_user.email,
                department='Computer Science',
                phone='Not specified',
                consultation_time='Not specified'
            )
            db.session.add(faculty_info)
            db.session.commit()
        
        if request.method == 'POST':
            try:
                # Update faculty profile
                faculty_info.name = request.form.get('name')
                faculty_info.phone = request.form.get('phone')
                faculty_info.department = request.form.get('department')
                faculty_info.consultation_time = request.form.get('consultation_time')
                
                # Update password if provided
                new_password = request.form.get('new_password')
                if new_password and new_password.strip():
                    faculty_info.set_password(new_password)
                
                db.session.commit()
                flash('✅ Profile updated successfully!', 'success')
                return redirect(url_for('faculty.faculty_profile'))
            except Exception as e:
                current_app.logger.error(f"Error updating faculty profile: {str(e)}")
                flash(f'❌ Error updating profile: {str(e)}', 'error')
        
        return render_template('faculty_profile.html', faculty_info=faculty_info)
    except Exception as e:
        current_app.logger.error(f"Error loading faculty profile: {str(e)}")
        flash('Error loading profile.', 'error')
        return redirect(url_for('faculty.faculty_dashboard'))

@faculty_bp.route('/faculty-analytics')
@faculty_required
def analytics():
    """View analytics with faculty privileges"""
    try:
        # Get basic statistics
        total_students = safe_execute(lambda: Student.query.count()) or 0
        total_results = safe_execute(lambda: Result.query.count()) or 0
        total_complaints = safe_execute(lambda: Complaint.query.count()) or 0
        
        return render_template('faculty_analytics.html',
                             total_students=total_students,
                             total_results=total_results,
                             total_complaints=total_complaints)
    except Exception as e:
        current_app.logger.error(f"Error loading faculty analytics: {str(e)}")
        flash('Error loading analytics.', 'error')
        return redirect(url_for('faculty.faculty_dashboard'))

# Additional faculty routes matching admin functionality
@faculty_bp.route('/edit-student/<int:student_id>', methods=['GET', 'POST'])
@faculty_required
def edit_student(student_id):
    """Edit student with faculty privileges"""
    student = Student.query.get_or_404(student_id)
    
    if request.method == 'POST':
        try:
            student.name = request.form.get('name')
            student.email = request.form.get('email')
            student.phone = request.form.get('phone')
            student.department = request.form.get('department')
            student.semester = request.form.get('semester')
            student.roll_number = request.form.get('roll_number')
            
            # Handle Telegram User ID update
            telegram_user_id = request.form.get('telegram_user_id')
            if telegram_user_id and telegram_user_id.strip():
                student.telegram_user_id = telegram_user_id.strip()
                student.telegram_verified = True
                # Also update the TelegramUserMapping table
                from app.models import TelegramUserMapping
                existing_mapping = TelegramUserMapping.query.filter_by(
                    phone_number=student.phone,
                    telegram_user_id=telegram_user_id.strip()
                ).first()
                
                if not existing_mapping:
                    mapping = TelegramUserMapping(
                        telegram_user_id=telegram_user_id.strip(),
                        student_id=student.id,
                        phone_number=student.phone,
                        verified=True
                    )
                    db.session.add(mapping)
            
            db.session.commit()
            flash('✅ Student updated successfully!', 'success')
            return redirect(url_for('faculty.faculty_manage_students'))
        except Exception as e:
            current_app.logger.error(f'Error updating student: {str(e)}')
            flash(f'❌ Error updating student: {str(e)}', 'error')
    
    return render_template('faculty_edit_student.html', student=student)
