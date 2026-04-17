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
from app.services.weekly_report_service import WeeklyReportService
from app.services.email_service import EmailService
from app.services.analytics_service import AnalyticsService
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
        # Get dashboard metrics
        total_students = Student.query.count() if Student else 0
        total_faculty = Faculty.query.count() if Faculty else 0
        active_notifications = Notification.query.count() if Notification else 0
        pending_complaints = Complaint.query.filter_by(status='pending').count() if Complaint else 0
        
        return render_template('admin_dashboard_edubot.html', 
                           total_students=total_students,
                           total_faculty=total_faculty,
                           total_notifications=active_notifications,
                           user=current_user)
    except Exception as e:
        current_app.logger.error(f"Error loading admin dashboard: {str(e)}")
        flash('Error loading dashboard. Please try again.', 'error')
        return render_template('admin_dashboard_edubot.html', 
                           total_students=0,
                           total_faculty=0,
                           total_notifications=0,
                           user=current_user)






@admin_bp.route('/refresh-activity', methods=['POST'])
@login_required
@admin_required
def refresh_activity():
    """Refresh real-time activity data"""
    try:
        # Get recent activities
        activities = []
        
        # Get recent notifications
        recent_notifications = Notification.query.order_by(
            Notification.created_at.desc()
        ).limit(5).all() if Notification else []
        
        # Convert notifications to activity format
        for notification in recent_notifications:
            activities.append({
                'text': f"New notification: {notification.title}",
                'time': format_time_ago(notification.created_at),
                'icon': 'bullhorn',
                'color': 'info'
            })
        
        # Get recent student registrations if any
        recent_students = Student.query.order_by(
            Student.created_at.desc()
        ).limit(3).all() if Student else []
        
        for student in recent_students:
            activities.append({
                'text': f"New student registered: {student.name}",
                'time': format_time_ago(student.created_at),
                'icon': 'user-graduate',
                'color': 'success'
            })
        
        return jsonify({
            'success': True,
            'activities': activities[:10]  # Limit to 10 most recent
        })
        
    except Exception as e:
        current_app.logger.error(f"Error refreshing activity: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'activities': []
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
        
        return render_template('manage_students.html', 
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
        faculty_members = Faculty.query.all()
        return render_template('manage_faculty.html', 
                           faculty_members=faculty_members,
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
        return render_template('add_faculty.html', user=current_user)
    
    try:
        # Get form data
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        department = request.form.get('department', '').strip()
        phone = request.form.get('phone', '').strip()
        consultation_time = request.form.get('consultation_time', '').strip()
        password = request.form.get('password', '').strip()
        send_credentials = request.form.get('send_credentials') == '1'
        
        # Validate
        if not name or not email:
            flash('Name and email are required.', 'error')
            return render_template('add_faculty.html', user=current_user)
        
        # Generate password if not provided
        if not password:
            # Generate simple password based on name
            first_name = name.split(' ')[0].lower()
            password = f"{first_name}123"
        
        # Create faculty
        faculty = Faculty(
            name=name,
            email=email,
            department=department,
            phone=phone,
            consultation_time=consultation_time,
            role='faculty'
        )
        
        # Set password if provided
        if password:
            faculty.set_password(password)
        
        db.session.add(faculty)
        db.session.commit()
        
        # Send credentials via email if requested
        if send_credentials:
            try:
                from app.services.email_service import EmailService
                
                subject = "Your Faculty Login Credentials - EduBot"
                body = f"""
Dear {name},

Your faculty account has been created successfully in the EduBot system.

Login Details:
- Email: {email}
- Password: {password}
- Login URL: {request.host_url}auth/login

Please change your password after first login for security.

Best regards,
EduBot Administration Team
"""
                
                html = f"""
<html>
<body>
    <h2>Welcome to EduBot Faculty Portal</h2>
    <p>Dear {name},</p>
    <p>Your faculty account has been created successfully in the EduBot system.</p>
    
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
        <h3>Login Details:</h3>
        <p><strong>Email:</strong> {email}</p>
        <p><strong>Password:</strong> <code>{password}</code></p>
        <p><strong>Login URL:</strong> <a href="{request.host_url}auth/login">{request.host_url}auth/login</a></p>
    </div>
    
    <p><strong>Important:</strong> Please change your password after first login for security.</p>
    
    <p>Best regards,<br>EduBot Administration Team</p>
</body>
</html>
"""
                
                email_sent = EmailService.send_email(email, subject, body, html)
                if email_sent:
                    flash('Faculty created successfully. Login credentials sent via email.', 'success')
                else:
                    flash('Faculty created successfully, but failed to send email. Please check email configuration.', 'warning')
            except Exception as e:
                current_app.logger.error(f"Error sending faculty credentials email: {str(e)}")
                flash('Faculty created successfully, but failed to send email. Please check email configuration.', 'warning')
        else:
            flash('Faculty created successfully.', 'success')
        
        return redirect(url_for('admin.manage_faculty'))
        
    except Exception as e:
        current_app.logger.error(f"Error creating faculty: {str(e)}")
        flash('Error creating faculty. Please try again.', 'error')
        return render_template('add_faculty.html', user=current_user)


@admin_bp.route('/add-faculty', methods=['GET', 'POST'])
@login_required
@admin_required
def add_faculty():
    """Add new faculty using existing template"""
    if request.method == 'GET':
        return render_template('add_faculty.html', user=current_user)
    
    try:
        # Get form data
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        department = request.form.get('department', '').strip()
        phone = request.form.get('phone', '').strip()
        consultation_time = request.form.get('consultation_time', '').strip()
        password = request.form.get('password', '').strip()
        send_credentials = request.form.get('send_credentials') == '1'
        
        # Validate
        if not name or not email:
            flash('Name and email are required.', 'error')
            return render_template('add_faculty.html', user=current_user)
        
        # Generate password if not provided
        if not password:
            # Generate simple password based on name
            first_name = name.split(' ')[0].lower()
            password = f"{first_name}123"
        
        # Create faculty
        faculty = Faculty(
            name=name,
            email=email,
            department=department,
            phone=phone,
            consultation_time=consultation_time,
            role='faculty'
        )
        
        # Set password if provided
        if password:
            faculty.set_password(password)
        
        db.session.add(faculty)
        db.session.commit()
        
        # Send credentials via email if requested
        if send_credentials:
            try:
                from app.services.email_service import EmailService
                
                subject = "Your Faculty Login Credentials - EduBot"
                body = f"""
Dear {name},

Your faculty account has been created successfully in the EduBot system.

Login Details:
- Email: {email}
- Password: {password}
- Login URL: {request.host_url}auth/login

Please change your password after first login for security.

Best regards,
EduBot Administration Team
"""
                
                html = f"""
<html>
<body>
    <h2>Welcome to EduBot Faculty Portal</h2>
    <p>Dear {name},</p>
    <p>Your faculty account has been created successfully in the EduBot system.</p>
    
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
        <h3>Login Details:</h3>
        <p><strong>Email:</strong> {email}</p>
        <p><strong>Password:</strong> <code>{password}</code></p>
        <p><strong>Login URL:</strong> <a href="{request.host_url}auth/login">{request.host_url}auth/login</a></p>
    </div>
    
    <p><strong>Important:</strong> Please change your password after first login for security.</p>
    
    <p>Best regards,<br>EduBot Administration Team</p>
</body>
</html>
"""
                
                email_sent = EmailService.send_email(email, subject, body, html)
                if email_sent:
                    flash('Faculty created successfully. Login credentials sent via email.', 'success')
                else:
                    flash('Faculty created successfully, but failed to send email. Please check email configuration.', 'warning')
            except Exception as e:
                current_app.logger.error(f"Error sending faculty credentials email: {str(e)}")
                flash('Faculty created successfully, but failed to send email. Please check email configuration.', 'warning')
        else:
            flash('Faculty created successfully.', 'success')
        
        return redirect(url_for('admin.manage_faculty'))
        
    except Exception as e:
        current_app.logger.error(f"Error creating faculty: {str(e)}")
        flash('Error creating faculty. Please try again.', 'error')
        return render_template('add_faculty.html', user=current_user)


@admin_bp.route('/edit-faculty/<int:faculty_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_faculty(faculty_id):
    """Edit faculty"""
    faculty = Faculty.query.get_or_404(faculty_id)
    
    if request.method == 'GET':
        return render_template('edit_faculty.html', 
                           faculty=faculty,
                           user=current_user)
    
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
            return render_template('edit_faculty.html', 
                               faculty=faculty,
                               user=current_user)
        
        # Update faculty
        faculty.name = name
        faculty.email = email
        faculty.department = department
        faculty.phone = phone
        faculty.consultation_time = consultation_time
        
        db.session.commit()
        
        flash('Faculty updated successfully.', 'success')
        return redirect(url_for('admin.manage_faculty'))
        
    except Exception as e:
        current_app.logger.error(f"Error updating faculty: {str(e)}")
        flash('Error updating faculty. Please try again.', 'error')
        return render_template('edit_faculty.html', 
                           faculty=faculty,
                           user=current_user)


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


@admin_bp.route('/add-student', methods=['GET', 'POST'])
@login_required
@admin_required
def add_student():
    """Add new student"""
    if request.method == 'GET':
        return render_template('add_student.html', user=current_user)
    
    try:
        # Get form data
        roll_number = request.form.get('roll_number', '').strip()
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()
        semester = request.form.get('semester', type=int)
        
        # Validate
        if not roll_number or not name or not phone:
            flash('Roll number, name, and phone are required.', 'error')
            return render_template('add_student.html', user=current_user)
        
        # Check if roll number already exists
        existing_student = Student.query.filter_by(roll_number=roll_number).first()
        if existing_student:
            flash('Roll number already exists.', 'error')
            return render_template('add_student.html', user=current_user)
        
        # Create student
        student = Student(
            roll_number=roll_number,
            name=name,
            email=email,
            phone=phone,
            department=department,
            semester=semester
        )
        
        db.session.add(student)
        db.session.commit()
        
        flash('Student added successfully.', 'success')
        return redirect(url_for('admin.manage_students'))
        
    except Exception as e:
        current_app.logger.error(f"Error adding student: {str(e)}")
        flash('Error adding student. Please try again.', 'error')
        return render_template('add_student.html', user=current_user)


@admin_bp.route('/edit-student/<int:student_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_student(student_id):
    """Edit student"""
    student = Student.query.get_or_404(student_id)
    
    if request.method == 'GET':
        return render_template('edit_student.html', 
                           student=student,
                           user=current_user)
    
    try:
        # Get form data
        roll_number = request.form.get('roll_number', '').strip()
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()
        semester = request.form.get('semester', type=int)
        
        # Validate
        if not roll_number or not name or not phone:
            flash('Roll number, name, and phone are required.', 'error')
            return render_template('edit_student.html', 
                               student=student,
                               user=current_user)
        
        # Check if roll number already exists (excluding current student)
        existing_student = Student.query.filter(
            Student.roll_number == roll_number,
            Student.id != student_id
        ).first()
        if existing_student:
            flash('Roll number already exists.', 'error')
            return render_template('edit_student.html', 
                               student=student,
                               user=current_user)
        
        # Update student
        student.roll_number = roll_number
        student.name = name
        student.email = email
        student.phone = phone
        student.department = department
        student.semester = semester
        
        db.session.commit()
        
        flash('Student updated successfully.', 'success')
        return redirect(url_for('admin.manage_students'))
        
    except Exception as e:
        current_app.logger.error(f"Error updating student: {str(e)}")
        flash('Error updating student. Please try again.', 'error')
        return render_template('edit_student.html', 
                           student=student,
                           user=current_user)


@admin_bp.route('/delete-student/<int:student_id>', methods=['POST'])
@login_required
@admin_required
def delete_student(student_id):
    """Delete student"""
    try:
        student = Student.query.get_or_404(student_id)
        db.session.delete(student)
        db.session.commit()
        
        flash('Student deleted successfully.', 'success')
        return redirect(url_for('admin.manage_students'))
        
    except Exception as e:
        current_app.logger.error(f"Error deleting student: {str(e)}")
        flash('Error deleting student. Please try again.', 'error')
        return redirect(url_for('admin.manage_students'))


@admin_bp.route('/upload')
@login_required
@admin_required
def upload():
    """Upload data page"""
    try:
        return render_template('admin_upload.html', user=current_user)
    except Exception as e:
        current_app.logger.error(f"Error loading upload page: {str(e)}")
        flash('Error loading upload page. Please try again.', 'error')
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
        
        return render_template('manage_notifications.html', 
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
        return render_template('add_notification.html', user=current_user)
    
    try:
        # Get form data
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        priority = request.form.get('priority', 'normal')
        expires_days = request.form.get('expires_days', 7, type=int)
        
        # Validate
        if not title or not content:
            flash('Title and content are required.', 'error')
            return render_template('add_notification.html', user=current_user)
        
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
        return render_template('add_notification.html', user=current_user)


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
        # Get query parameters
        search = request.args.get('search', '').strip()
        selected_section = request.args.get('section', '').strip()
        
        # Build query
        query = PredefinedInfo.query
        
        # Apply section filter
        if selected_section:
            query = query.filter(PredefinedInfo.section == selected_section)
        
        # Apply search filter
        if search:
            search_pattern = f'%{search}%'
            query = query.filter(
                db.or_(
                    PredefinedInfo.title.ilike(search_pattern),
                    PredefinedInfo.content.ilike(search_pattern),
                    PredefinedInfo.category.ilike(search_pattern)
                )
            )
        
        # Order and execute
        predefined_info = query.order_by(
            PredefinedInfo.section, PredefinedInfo.title
        ).all()
        
        # Define available sections
        sections = [
            ('admission', 'Admission'),
            ('fees', 'Fees'),
            ('facilities', 'Facilities'),
            ('courses', 'Courses'),
            ('academic', 'Academic Calendar'),
            ('contact', 'Contact Information'),
            ('library', 'Library'),
            ('hostel', 'Hostel'),
            ('transport', 'Transport'),
            ('sports', 'Sports'),
            ('placement', 'Placement'),
            ('general', 'General')
        ]
        
        return render_template('manage_predefined_info.html', 
                           info_pagination=type('Pagination', (), {'items': predefined_info, 'total': len(predefined_info), 'pages': 1, 'page': 1, 'has_prev': False, 'has_next': False, 'prev_num': 1, 'next_num': 1})(),
                           predefined_info=predefined_info,
                           sections=sections,
                           selected_section=selected_section,
                           search=search,
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


# Analytics Routes
@admin_bp.route('/analytics')
@login_required
def analytics():
    """Analytics dashboard page"""
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('admin.admin_dashboard'))
    
    try:
        # Get analytics data
        analytics_data = AnalyticsService.get_analytics()
        weekly_data = AnalyticsService.get_weekly_report_data()
        
        return render_template('analytics.html', 
                           analytics=analytics_data,
                           weekly_data=weekly_data,
                           admin_email=Config.ADMIN_EMAIL or 'uniyalanuj1@gmail.com',
                           user=current_user)
    except Exception as e:
        current_app.logger.error(f"Error loading analytics: {str(e)}")
        flash('Error loading analytics. Please try again.', 'error')
        return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/analytics-data')
@login_required
def analytics_data():
    """API endpoint for analytics data"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin privileges required'}), 403
    
    try:
        # Get analytics data
        analytics_data = AnalyticsService.get_analytics()
        
        # Get weekly report data
        weekly_data = AnalyticsService.get_weekly_report_data()
        
        # Generate mock weekly trend data (in real implementation, this would come from database)
        import random
        weekly_trend = {
            'total': [random.randint(10, 50) for _ in range(7)],
            'unknown': [random.randint(1, 10) for _ in range(7)]
        }
        
        # Merge data
        analytics_data.update({
            'weekly_data': weekly_trend,
            'success_rate': analytics_data.get('success_rate', 0)
        })
        analytics_data.update(weekly_data)
        
        return jsonify(analytics_data)
        
    except Exception as e:
        current_app.logger.error(f"Error getting analytics data: {str(e)}")
        return jsonify({
            'error': str(e),
            'total_queries': 0,
            'unknown_queries': 0,
            'registered_students': 0,
            'top_unknown': [],
            'weekly_data': {'total': [], 'unknown': []}
        }), 500


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


@admin_bp.route('/bot-status')
@login_required
@admin_required
def bot_status():
    """Get bot status"""
    try:
        # Check if bot token is configured
        bot_token = current_app.config.get('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            return jsonify({
                'status': 'inactive',
                'message': 'Bot token not configured',
                'last_check': datetime.utcnow().isoformat()
            })
        
        # Check bot webhook status
        import requests
        webhook_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
        response = requests.get(webhook_url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                webhook_info = result.get('result', {})
                webhook_url_set = webhook_info.get('url', '')
                
                if webhook_url_set:
                    return jsonify({
                        'status': 'active',
                        'message': 'Bot is running with webhook',
                        'webhook_url': webhook_url_set,
                        'last_check': datetime.utcnow().isoformat()
                    })
                else:
                    return jsonify({
                        'status': 'inactive',
                        'message': 'Bot webhook not set',
                        'last_check': datetime.utcnow().isoformat()
                    })
            else:
                return jsonify({
                    'status': 'error',
                    'message': f"Bot API error: {result.get('description', 'Unknown error')}",
                    'last_check': datetime.utcnow().isoformat()
                })
        else:
            return jsonify({
                'status': 'error',
                'message': f"HTTP error: {response.status_code}",
                'last_check': datetime.utcnow().isoformat()
            })
            
    except Exception as e:
        current_app.logger.error(f"Error checking bot status: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error checking bot status: {str(e)}",
            'last_check': datetime.utcnow().isoformat()
        }), 500


@admin_bp.route('/toggle-bot', methods=['POST'])
@login_required
@admin_required
def toggle_bot():
    """Toggle bot status"""
    try:
        data = request.get_json()
        action = data.get('action')
        
        if action not in ['activate', 'deactivate']:
            return jsonify({
                'success': False,
                'message': 'Invalid action. Use "activate" or "deactivate"'
            }), 400
        
        bot_token = current_app.config.get('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            return jsonify({
                'success': False,
                'message': 'Bot token not configured'
            }), 400
        
        import requests
        
        if action == 'activate':
            # Set webhook to activate bot
            webhook_url = current_app.config.get('PUBLIC_BASE_URL', 'https://localhost:5000')
            if not webhook_url.endswith('/telegram/webhook'):
                webhook_url = webhook_url.rstrip('/') + '/telegram/webhook'
            
            # For local development, check if we're using HTTP and provide guidance
            if webhook_url.startswith('http://localhost'):
                return jsonify({
                    'success': False,
                    'message': 'Telegram requires HTTPS URLs for webhooks. For local development, use ngrok or another tunneling service to get an HTTPS URL, or set PUBLIC_BASE_URL environment variable to your HTTPS URL.'
                }), 400
            
            current_app.logger.info(f"Attempting to activate bot with webhook: {webhook_url}")
            current_app.logger.info(f"Bot token configured: {'Yes' if bot_token else 'No'}")
            
            set_webhook_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
            data = {
                'url': webhook_url,
                'allowed_updates': ['message']
            }
            
            current_app.logger.info(f"Sending webhook request to: {set_webhook_url}")
            response = requests.post(set_webhook_url, json=data, timeout=10)
            current_app.logger.info(f"Webhook response status: {response.status_code}")
            current_app.logger.info(f"Webhook response body: {response.text}")
            
            try:
                result = response.json()
                current_app.logger.info(f"Telegram API response: {result}")
                
                if result.get('ok'):
                    current_app.logger.info("Bot activated successfully")
                    return jsonify({
                        'success': True,
                        'message': 'Bot activated successfully',
                        'webhook_url': webhook_url
                    })
                else:
                    error_msg = result.get('description', 'Unknown error')
                    error_code = result.get('error_code', 'N/A')
                    current_app.logger.error(f"Telegram API error: {error_msg} (Code: {error_code})")
                    return jsonify({
                        'success': False,
                        'message': f"Failed to activate bot: {error_msg}",
                        'error_code': error_code
                    })
            except ValueError as e:
                current_app.logger.error(f"Invalid JSON response from Telegram: {e}")
                return jsonify({
                    'success': False,
                    'message': 'Invalid response from Telegram API'
                })
            except Exception as e:
                current_app.logger.error(f"Unexpected error processing response: {e}")
                return jsonify({
                    'success': False,
                    'message': f"Error processing bot activation: {str(e)}"
                })
            
            if response.status_code != 200:
                current_app.logger.error(f"HTTP error {response.status_code}: {response.text}")
                return jsonify({
                    'success': False,
                    'message': f"HTTP error activating bot: {response.status_code}",
                    'response_text': response.text
                })
        
        elif action == 'deactivate':
            # Delete webhook to deactivate bot
            delete_webhook_url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
            response = requests.post(delete_webhook_url, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    current_app.logger.info("Bot deactivated successfully")
                    return jsonify({
                        'success': True,
                        'message': 'Bot deactivated successfully'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': f"Failed to deactivate bot: {result.get('description', 'Unknown error')}"
                    })
            else:
                return jsonify({
                    'success': False,
                    'message': f"HTTP error deactivating bot: {response.status_code}"
                })
        
    except Exception as e:
        current_app.logger.error(f"Error toggling bot: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error toggling bot: {str(e)}"
        }), 500
