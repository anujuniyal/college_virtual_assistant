from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app.extensions import db
from app.models import Student, Faculty, Notification, Complaint, Result, FeeRecord, StudentRegistration, QueryLog, FAQRecord, ChatbotQA, PredefinedInfo, FAQ
from app.services.safe_execute import safe_execute
from datetime import datetime, timedelta
import json

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """Decorator to ensure user has admin privileges"""
    def admin_decorated_function(*args, **kwargs):
        if not current_user or not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        # Handle both Admin and Faculty models
        if hasattr(current_user, 'role'):
            user_role = current_user.role
        elif hasattr(current_user, 'user_role'):
            user_role = current_user.user_role
        else:
            user_role = 'student'
        
        if user_role != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    # Preserve to original function name for URL generation
    admin_decorated_function.__name__ = f.__name__
    return admin_decorated_function

def faculty_required(f):
    """Decorator to ensure user has faculty privileges"""
    def faculty_decorated_function(*args, **kwargs):
        if not current_user or not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        # Handle both Admin and Faculty models
        if hasattr(current_user, 'role'):
            user_role = current_user.role
        elif hasattr(current_user, 'user_role'):
            user_role = current_user.user_role
        else:
            user_role = 'student'
        
        if user_role not in ['admin', 'faculty']:
            flash('Access denied. Faculty privileges required.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    # Preserve to original function name for URL generation
    faculty_decorated_function.__name__ = f.__name__
    return faculty_decorated_function

def _sync_telegram_mappings():
    """Sync existing Telegram mappings to student records"""
    try:
        from app.models import TelegramUserMapping
        
        # Find all verified mappings where student.telegram_user_id is not set
        unmapped_students = db.session.query(Student, TelegramUserMapping).join(
            TelegramUserMapping, Student.id == TelegramUserMapping.student_id
        ).filter(
            TelegramUserMapping.verified == True,
            Student.telegram_user_id.is_(None)
        ).all()
        
        synced_count = 0
        for student, mapping in unmapped_students:
            success, message = student.link_telegram_account(mapping.telegram_user_id)
            if success:
                synced_count += 1
                current_app.logger.info(f"Auto-synced Telegram ID for student {student.name} ({student.roll_number})")
            else:
                current_app.logger.warning(f"Failed to auto-sync Telegram ID for {student.name}: {message}")
        
        if synced_count > 0:
            current_app.logger.info(f"Auto-synced {synced_count} student Telegram mappings")
        
        return synced_count
    except Exception as e:
        current_app.logger.error(f"Error syncing Telegram mappings: {str(e)}")
        return 0

@admin_bp.route('/dashboard')
@login_required
def admin_dashboard_main():
    """Role-based dashboard"""
    try:
        # Handle both Admin and Faculty models for role detection
        if hasattr(current_user, 'role'):
            user_role = current_user.role
        elif hasattr(current_user, 'user_role'):
            user_role = current_user.user_role
        else:
            user_role = 'student'
        
        # Get statistics based on role
        if user_role == 'admin':
            return _admin_dashboard()
        elif user_role == 'faculty':
            return _faculty_dashboard()
        elif user_role == 'accounts':
            return _accounts_dashboard()
        else:
            flash('Invalid user role.', 'error')
            return redirect(url_for('auth.login'))
    
    except Exception as e:
        current_app.logger.error(f"Dashboard error: {str(e)}")
        flash('Error loading dashboard.', 'error')
        return redirect(url_for('auth.login'))

def _admin_dashboard():
    """Admin dashboard with full access"""
    try:
        # Get comprehensive statistics
        total_students = safe_execute(lambda: Student.query.count()) or 0
        total_faculty = safe_execute(lambda: Faculty.query.count()) or 0
        
        # Auto-sync any missing Telegram mappings
        synced_count = _sync_telegram_mappings()
        if synced_count > 0:
            flash(f'🔄 Auto-synced {synced_count} student Telegram accounts', 'info')
        
        total_notifications = safe_execute(
            lambda: Notification.query.filter(
                Notification.expires_at > datetime.utcnow()
            ).count()
        ) or 0
        pending_complaints = safe_execute(
            lambda: Complaint.query.filter_by(status='pending').count()
        ) or 0
        
        # Get recent notifications
        recent_notifications = safe_execute(
            lambda: Notification.query.order_by(Notification.created_at.desc()).limit(5).all()
        ) or []
        
        # Get bot status
        bot_status = _get_bot_status()
        
        return render_template('admin_dashboard_edubot.html',
                             total_students=total_students,
                             total_faculty=total_faculty,
                             total_notifications=total_notifications,
                             pending_complaints=pending_complaints,
                             recent_notifications=recent_notifications,
                             bot_status=bot_status)
    
    except Exception as e:
        current_app.logger.error(f"Admin dashboard error: {str(e)}")
        flash('Error loading admin dashboard.', 'error')
        # Get recent notifications
        recent_notifications = safe_execute(
            lambda: Notification.query.order_by(Notification.created_at.desc()).limit(5).all()
        ) or []
        
        # Get bot status
        bot_status = _get_bot_status()
        
        return render_template('admin_dashboard_edubot.html',
                             total_students=0,
                             total_faculty=0,
                             total_notifications=0,
                             pending_complaints=0,
                             recent_notifications=[],
                             bot_status=bot_status)

def _faculty_dashboard():
    """Faculty dashboard with limited access"""
    try:
        # Get faculty-specific statistics
        total_students = safe_execute(lambda: Student.query.count()) or 0
        total_notifications = safe_execute(lambda: Notification.query.filter_by(notification_type='general').count()) or 0
        
        # Create faculty_info dict with required attributes
        faculty_info = {
            'name': current_user.username,
            'email': current_user.email,
            'department': 'Computer Science',  # Default department
            'phone': 'Not specified',  # Default phone
            'consultation_time': 'Not specified'  # Default consultation time
        }
        
        # Get recent notifications
        recent_notifications = safe_execute(
            lambda: Notification.query.order_by(Notification.created_at.desc()).limit(5).all()
        ) or []
        
        # Get bot status
        bot_status = _get_bot_status()
        
        # Get recent activities from database
        recent_activities = _get_recent_activities()
        
        return render_template('faculty_dashboard_edubot.html',
                             faculty_info=faculty_info,
                             total_students=total_students,
                             total_notifications=total_notifications,
                             recent_notifications=recent_notifications,
                             bot_status=bot_status,
                             recent_activities=recent_activities)
    except Exception as e:
        current_app.logger.error(f"Faculty dashboard error: {str(e)}")
        flash('Error loading faculty dashboard.', 'error')
        # Get recent notifications
        recent_notifications = safe_execute(
            lambda: Notification.query.order_by(Notification.created_at.desc()).limit(5).all()
        ) or []
        
        # Get bot status
        bot_status = _get_bot_status()
        
        # Get recent activities from database
        recent_activities = _get_recent_activities()
        
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
                             recent_notifications=[],
                             bot_status=bot_status,
                             recent_activities=[])

def _accounts_dashboard():
    """Accounts dashboard with financial access"""
    try:
        # Get accounts-specific statistics
        total_students = safe_execute(lambda: Student.query.count()) or 0
        total_faculty = safe_execute(lambda: Faculty.query.count()) or 0
        
        return render_template('accounts_dashboard_edubot.html',
                             total_students=total_students,
                             total_faculty=total_faculty)
    except Exception as e:
        current_app.logger.error(f"Accounts dashboard error: {str(e)}")
        flash('Error loading accounts dashboard.', 'error')
        return render_template('accounts_dashboard_edubot.html',
                             total_students=0,
                             total_faculty=0)

@admin_bp.route('/dashboard-data')
@admin_required
def admin_dashboard_data():
    """AJAX endpoint for dashboard data refresh"""
    try:
        # Get fresh statistics
        total_students = safe_execute(lambda: Student.query.count()) or 0
        total_faculty = safe_execute(lambda: Faculty.query.count()) or 0
        total_notifications = safe_execute(
            lambda: Notification.query.filter(
                Notification.expires_at > datetime.utcnow()
            ).count()
        ) or 0
        pending_complaints = safe_execute(
            lambda: Complaint.query.filter_by(status='pending').count()
        ) or 0
        
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
                'created_at': notif.created_at.strftime('%d %b %Y, %I:%M %p') if notif.created_at else 'N/A'
            })
        
        # Get bot status and recent activities
        bot_status = _get_bot_status()
        recent_activities = _get_recent_activities()
        
        return jsonify({
            'success': True,
            'total_students': total_students,
            'total_faculty': total_faculty,
            'total_notifications': total_notifications,
            'pending_complaints': pending_complaints,
            'recent_notifications': recent_notifications_data,
            'bot_status': bot_status,
            'recent_activities': recent_activities
        })
        
    except Exception as e:
        current_app.logger.error(f"Dashboard data AJAX error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error loading dashboard data'
        }), 500

@admin_bp.route('/add-student', methods=['GET', 'POST'])
@admin_required
def add_student():
    """Add new student"""
    if request.method == 'POST':
        try:
            telegram_user_id = request.form.get('telegram_user_id')
            telegram_verified = False
            
            if telegram_user_id and telegram_user_id.strip():
                telegram_verified = True
                # Create TelegramUserMapping entry
                from app.models import TelegramUserMapping
                mapping = TelegramUserMapping(
                    telegram_user_id=telegram_user_id.strip(),
                    phone_number=request.form.get('phone'),
                    verified=True
                )
                # We'll add this after the student is created
            
            student = Student(
                name=request.form.get('name'),
                email=request.form.get('email'),
                phone=request.form.get('phone'),
                department=request.form.get('department'),
                semester=request.form.get('semester'),
                roll_number=request.form.get('roll_number'),
                telegram_user_id=telegram_user_id.strip() if telegram_user_id else None,
                telegram_verified=telegram_verified
            )
            
            db.session.add(student)
            db.session.commit()
            
            # Add TelegramUserMapping if needed
            if telegram_verified:
                mapping.student_id = student.id
                db.session.add(mapping)
                db.session.commit()
                
                # Also use the student's link_telegram_account method for consistency
                success, message = student.link_telegram_account(telegram_user_id.strip())
                if not success:
                    current_app.logger.warning(f"Failed to link Telegram account: {message}")
            flash('✅ Student added successfully!', 'success')
            return redirect(url_for('admin.admin_dashboard_main'))
        except Exception as e:
            current_app.logger.error(f"Error adding student: {str(e)}")
            flash(f'❌ Error adding student: {str(e)}', 'error')
    
    return render_template('add_student.html')

@admin_bp.route('/manage-students')
@admin_required
def manage_students():
    """Manage all students"""
    try:
        students = safe_execute(
            lambda: Student.query.order_by(Student.name).all()
        ) or []
        return render_template('manage_students.html', students=students)
    except Exception as e:
        current_app.logger.error(f"Error loading manage students: {str(e)}")
        flash('Error loading students.', 'error')
        return render_template('manage_students.html', students=[])

@admin_bp.route('/edit-student/<int:student_id>', methods=['GET', 'POST'])
@admin_required
def edit_student(student_id):
    """Edit existing student"""
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
                # Use the student's link_telegram_account method for proper linking
                success, message = student.link_telegram_account(telegram_user_id.strip())
                if success:
                    current_app.logger.info(f"Successfully linked Telegram account for student {student.name}")
                else:
                    current_app.logger.warning(f"Failed to link Telegram account: {message}")
            
            db.session.commit()
            flash('✅ Student updated successfully!', 'success')
            return redirect(url_for('admin.manage_students'))
        except Exception as e:
            current_app.logger.error(f"Error updating student: {str(e)}")
            flash(f'❌ Error updating student: {str(e)}', 'error')
    
    return render_template('edit_student.html', student=student)

@admin_bp.route('/delete-student/<int:student_id>', methods=['GET', 'POST'])
@admin_required
def delete_student(student_id):
    """Delete student with proper cascade handling"""
    try:
        student = Student.query.get_or_404(student_id)
        
        # Delete related records first to avoid foreign key constraints
        from app.models import Result, FeeRecord, TelegramUserMapping, QueryLog, Complaint
        
        # Delete related results
        Result.query.filter_by(student_id=student_id).delete()
        
        # Delete related fee records
        FeeRecord.query.filter_by(student_id=student_id).delete()
        
        # Delete related telegram mappings
        TelegramUserMapping.query.filter_by(student_id=student_id).delete()
        
        # Delete related query logs
        QueryLog.query.filter_by(student_id=student_id).delete()
        
        # Delete complaints related to the student
        Complaint.query.filter_by(student_id=student_id).delete()
        
        # Now delete the student
        db.session.delete(student)
        db.session.commit()
        
        flash('✅ Student deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting student: {str(e)}")
        flash(f'❌ Error deleting student: {str(e)}', 'error')
    
    return redirect(url_for('admin.manage_students'))

@admin_bp.route('/manage-faculty')
@admin_required
def manage_faculty():
    """Manage all faculty"""
    try:
        faculty_members = safe_execute(
            lambda: Faculty.query.order_by(Faculty.name).all()
        ) or []
        return render_template('manage_faculty.html', faculty_members=faculty_members)
    except Exception as e:
        current_app.logger.error(f"Error loading manage faculty: {str(e)}")
        flash('Error loading faculty.', 'error')
        return render_template('manage_faculty.html', faculty_members=[])

@admin_bp.route('/add-faculty', methods=['GET', 'POST'])
@admin_required
def add_faculty():
    """Add new faculty member"""
    if request.method == 'POST':
        try:
            # Get role from form, default to 'faculty' if not provided
            role = request.form.get('role', 'faculty')
            
            faculty = Faculty(
                name=request.form.get('name'),
                email=request.form.get('email'),
                phone=request.form.get('phone'),
                department=request.form.get('department'),
                consultation_time=request.form.get('consultation_time'),
                role=role  # Set the role from form
            )
            
            # Set password if provided
            password = request.form.get('password')
            if password:
                faculty.set_password(password)
            
            db.session.add(faculty)
            db.session.commit()
            
            # Send credentials email if requested
            send_credentials = request.form.get('send_credentials') == '1'
            if send_credentials and password:
                try:
                    from app.services.email_service import EmailService
                    subject = "Your Faculty Login Credentials - College Virtual Assistant"
                    body = f"""
Dear {faculty.name},

Your faculty account has been created successfully in the College Virtual Assistant system.

Login Details:
- Email: {faculty.email}
- Password: {password}
- Role: {faculty.role}

You can now access the faculty dashboard using these credentials.

Important:
- Please change your password after first login
- Keep your credentials secure
- Contact admin if you face any issues

Best regards,
College Administration
"""
                    
                    success = EmailService.send_email(faculty.email, subject, body)
                    if success:
                        flash('Faculty added successfully! Credentials sent to email.', 'success')
                    else:
                        flash('Faculty added successfully! (Email notification failed)', 'warning')
                except Exception as e:
                    current_app.logger.error(f"Error sending faculty credentials email: {str(e)}")
                    flash('Faculty added successfully! (Email notification failed)', 'warning')
            else:
                flash('Faculty added successfully!', 'success')
            
            return redirect(url_for('admin.manage_faculty'))
        except Exception as e:
            current_app.logger.error(f"Error adding faculty: {str(e)}")
            flash(f'❌ Error adding faculty: {str(e)}', 'error')
    
    return render_template('add_faculty.html')

@admin_bp.route('/edit-faculty/<int:faculty_id>', methods=['GET', 'POST'])
@admin_required
def edit_faculty(faculty_id):
    """Edit existing faculty"""
    faculty = Faculty.query.get_or_404(faculty_id)
    
    if request.method == 'POST':
        try:
            faculty.name = request.form.get('name')
            faculty.email = request.form.get('email')
            faculty.phone = request.form.get('phone')
            faculty.department = request.form.get('department')
            faculty.consultation_time = request.form.get('consultation_time')
            
            # Handle role update
            new_role = request.form.get('role')
            if new_role and new_role.strip():
                valid_roles = ['admin', 'faculty', 'accounts']
                if new_role in valid_roles:
                    faculty.role = new_role
                else:
                    flash(f'❌ Invalid role: {new_role}. Valid roles are: {", ".join(valid_roles)}', 'error')
                    return render_template('edit_faculty.html', faculty=faculty)
            
            # Handle password update if provided
            password = request.form.get('password')
            if password and password.strip():
                faculty.set_password(password)
            
            db.session.commit()
            flash('✅ Faculty updated successfully!', 'success')
            return redirect(url_for('admin.manage_faculty'))
        except Exception as e:
            current_app.logger.error(f"Error updating faculty: {str(e)}")
            flash(f'❌ Error updating faculty: {str(e)}', 'error')
    
    return render_template('edit_faculty.html', faculty=faculty)

@admin_bp.route('/delete-faculty/<int:faculty_id>', methods=['GET', 'POST'])
@admin_required
def delete_faculty(faculty_id):
    """Delete faculty"""
    try:
        faculty = Faculty.query.get_or_404(faculty_id)
        db.session.delete(faculty)
        db.session.commit()
        flash('✅ Faculty deleted successfully!', 'success')
    except Exception as e:
        current_app.logger.error(f"Error deleting faculty: {str(e)}")
        flash(f'❌ Error deleting faculty: {str(e)}', 'error')
    
    return redirect(url_for('admin.manage_faculty'))

@admin_bp.route('/add-notification', methods=['GET', 'POST'])
@admin_required
def add_notification():
    """Add new notification"""
    # Check if this is an AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if request.method == 'POST':
        try:
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
                    return render_template('add_notification.html')
            
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
                return redirect(url_for('admin.admin_dashboard_main'))
            
        except Exception as e:
            current_app.logger.error(f"Error adding notification: {str(e)}")
            db.session.rollback()
            
            error_msg = f'❌ Error adding notification: {str(e)}'
            if is_ajax:
                return jsonify({
                    'success': False,
                    'message': error_msg
                })
            else:
                flash(error_msg, 'error')
    
    return render_template('add_notification.html')


## Telegram mapping is now automatic via "Share phone number" contact flow in Telegram.

@admin_bp.route('/analytics')
@admin_required
def analytics():
    """View analytics dashboard"""
    try:
        # Get basic statistics
        total_students = safe_execute(lambda: Student.query.count()) or 0
        total_faculty = safe_execute(lambda: Faculty.query.count()) or 0
        total_notifications = safe_execute(lambda: Notification.query.count()) or 0
        total_complaints = safe_execute(lambda: Complaint.query.count()) or 0
        total_results = safe_execute(lambda: Result.query.count()) or 0
        total_fee_records = safe_execute(lambda: FeeRecord.query.count()) or 0
        
        # Get real query data
        from datetime import datetime, timedelta
        today = datetime.utcnow().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Query logs for real metrics
        result_queries_today = safe_execute(
            lambda: QueryLog.query.filter(
                QueryLog.query_type == 'result',
                QueryLog.query_date == today
            ).count()
        ) or 0
        
        result_queries_week = safe_execute(
            lambda: QueryLog.query.filter(
                QueryLog.query_type == 'result',
                QueryLog.query_date >= week_ago
            ).count()
        ) or 0
        
        fee_queries_today = safe_execute(
            lambda: QueryLog.query.filter(
                QueryLog.query_type == 'fee',
                QueryLog.query_date == today
            ).count()
        ) or 0
        
        fee_queries_week = safe_execute(
            lambda: QueryLog.query.filter(
                QueryLog.query_type == 'fee',
                QueryLog.query_date >= week_ago
            ).count()
        ) or 0
        
        total_queries_today = safe_execute(
            lambda: QueryLog.query.filter(
                QueryLog.query_date == today
            ).count()
        ) or 0
        
        # Chatbot unknown queries
        try:
            unknown_queries = safe_execute(lambda: db.session.query(FAQRecord).count()) or 0
            unknown_queries_week = safe_execute(
                lambda: db.session.query(FAQRecord).filter(
                    FAQRecord.created_at >= datetime.utcnow() - timedelta(days=7)
                ).count()
            ) or 0
        except Exception as e:
            current_app.logger.warning(f"FAQRecord query failed: {e}")
            unknown_queries = 0
            unknown_queries_week = 0
        
        # Recent activity data
        recent_notifications = safe_execute(
            lambda: Notification.query.filter(
                Notification.created_at >= datetime.utcnow() - timedelta(days=7)
            ).order_by(Notification.created_at.desc()).limit(5).all()
        ) or []
        
        # Department statistics
        dept_stats = safe_execute(
            lambda: db.session.query(
                Student.department, 
                db.func.count(Student.id).label('count')
            ).group_by(Student.department).all()
        ) or []
        
        # Get top unknown questions
        try:
            from app.services.analytics_service import AnalyticsService
            top_unknown_data = AnalyticsService.get_weekly_report_data()
            top_unknown = top_unknown_data.get('top_unknown', [])
        except Exception as e:
            current_app.logger.warning(f"Failed to get top unknown questions: {e}")
            top_unknown = []
        
        # Prepare analytics data structure with real database data only
        analytics_data = {
            'total_queries': total_notifications + total_complaints + total_queries_today,
            'unknown_queries': unknown_queries,
            'registered_students': total_students,
            'result_queries_today': result_queries_today,
            'result_queries_week': result_queries_week,
            'fee_queries_today': fee_queries_today,
            'fee_queries_week': fee_queries_week,
            'total_queries_today': total_queries_today,
            'total_results': total_results,
            'total_fee_records': total_fee_records,
            'recent_notifications': recent_notifications,
            'department_stats': dept_stats,
            'unknown_queries_week': unknown_queries_week,
            'top_unknown': top_unknown
        }
        
        return render_template('analytics.html',
                             analytics=analytics_data,
                             total_students=total_students,
                             total_faculty=total_faculty,
                             total_notifications=total_notifications,
                             total_complaints=total_complaints,
                             total_results=total_results,
                             total_fee_records=total_fee_records)
    except Exception as e:
        current_app.logger.error(f"Error loading analytics: {str(e)}")
        flash('Error loading analytics.', 'error')
        return redirect(url_for('admin.admin_dashboard_main'))

@admin_bp.route('/college-accounts')
@admin_required
def college_accounts():
    """Manage college accounts and finances"""
    try:
        # Get accounts data
        total_students = safe_execute(lambda: Student.query.count()) or 0
        total_faculty = safe_execute(lambda: Faculty.query.count()) or 0
        
        return render_template('manage_accounts.html',
                             total_students=total_students,
                             total_faculty=total_faculty)
    except Exception as e:
        current_app.logger.error(f"Error loading college accounts: {str(e)}")
        flash('Error loading accounts.', 'error')
        return redirect(url_for('admin.admin_dashboard_main'))

@admin_bp.route('/register')
@admin_required
def register():
    """Student registration page - redirect to registrations"""
    return redirect(url_for('admin.student_registrations'))


@admin_bp.route('/performance-debug')
def performance_debug():
    """Debug performance page without authentication"""
    try:
        return render_template('performance_debug.html')
    except Exception as e:
        return f"Error loading debug page: {str(e)}"


@admin_bp.route('/performance-test')
@login_required
@admin_required
def performance_test():
    """Simple performance test page without navigation"""
    try:
        # Get basic metrics
        total_students = safe_execute(lambda: Student.query.count()) or 0
        total_faculty = safe_execute(lambda: Faculty.query.count()) or 0
        
        return render_template('performance_test.html',
                             total_students=total_students,
                             total_faculty=total_faculty)
    except Exception as e:
        current_app.logger.error(f"Error loading performance test: {str(e)}")
        return "Error loading performance test"

# Additional admin routes for faculty management
@admin_bp.route('/faculty-profile')
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
        
        return render_template('faculty_profile.html', faculty_info=faculty_info)
    except Exception as e:
        current_app.logger.error(f"Error loading faculty profile: {str(e)}")
        flash('Error loading profile.', 'error')
        return redirect(url_for('admin.admin_dashboard_main'))

@admin_bp.route('/faculty-manage-results')
@faculty_required
def faculty_manage_results():
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

@admin_bp.route('/manage-complaints')
@admin_required
def manage_complaints():
    """Manage all complaints"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        status_filter = request.args.get('status', '')
        category_filter = request.args.get('category', '')
        
        # Build query
        query = Complaint.query
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        if category_filter:
            query = query.filter_by(category=category_filter)
        
        # Paginate
        complaints_pagination = query.order_by(Complaint.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Get statistics
        total_complaints = safe_execute(lambda: Complaint.query.count()) or 0
        pending_complaints = safe_execute(
            lambda: Complaint.query.filter_by(status='pending').count()
        ) or 0
        investigating_complaints = safe_execute(
            lambda: Complaint.query.filter_by(status='investigating').count()
        ) or 0
        resolved_complaints = safe_execute(
            lambda: Complaint.query.filter_by(status='resolved').count()
        ) or 0
        
        return render_template('manage_complaints.html',
                             complaints_pagination=complaints_pagination,
                             total_complaints=total_complaints,
                             pending_complaints=pending_complaints,
                             investigating_complaints=investigating_complaints,
                             resolved_complaints=resolved_complaints,
                             selected_status=status_filter,
                             selected_category=category_filter)
    except Exception as e:
        current_app.logger.error(f"Error loading manage complaints: {str(e)}")
        flash('Error loading complaints.', 'error')
        return render_template('manage_complaints.html',
                             complaints_pagination=None,
                             total_complaints=0,
                             pending_complaints=0,
                             investigating_complaints=0,
                             resolved_complaints=0)

@admin_bp.route('/view-complaint/<int:complaint_id>')
@admin_required
def view_complaint(complaint_id):
    """View individual complaint details"""
    try:
        complaint = Complaint.query.get_or_404(complaint_id)
        return render_template('view_complaint.html', complaint=complaint)
    except Exception as e:
        current_app.logger.error(f"Error viewing complaint: {str(e)}")
        flash('Error loading complaint details.', 'error')
        return redirect(url_for('admin.manage_complaints'))

@admin_bp.route('/update-complaint-status/<int:complaint_id>', methods=['POST'])
@admin_required
def update_complaint_status(complaint_id):
    """Update complaint status"""
    try:
        complaint = Complaint.query.get_or_404(complaint_id)
        new_status = request.form.get('status')
        
        if new_status not in ['pending', 'investigating', 'resolved']:
            flash('Invalid status.', 'error')
            return redirect(url_for('admin.view_complaint', complaint_id=complaint_id))
        
        old_status = complaint.status
        complaint.status = new_status
        db.session.commit()
        
        # Send notifications about status update
        try:
            from app.services.complaint_notification_service import ComplaintNotificationService
            from app.models import Student
            
            student = Student.query.get(complaint.student_id)
            if student:
                # Send admin notification
                ComplaintNotificationService.notify_complaint_status_update(
                    complaint_id=complaint_id,
                    old_status=old_status,
                    new_status=new_status,
                    student_name=student.name
                )
                
                # Send Telegram notification to student
                ComplaintNotificationService.notify_student_telegram(
                    complaint_id=complaint_id,
                    old_status=old_status,
                    new_status=new_status,
                    student_id=complaint.student_id
                )
        except Exception as e:
            current_app.logger.error(f"Error sending status update notification: {str(e)}")
        
        flash(f'✅ Complaint status updated from {old_status} to {new_status}', 'success')
        return redirect(url_for('admin.view_complaint', complaint_id=complaint_id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating complaint status: {str(e)}")
        flash(f'❌ Error updating complaint status: {str(e)}', 'error')
        return redirect(url_for('admin.view_complaint', complaint_id=complaint_id))

@admin_bp.route('/delete-complaint/<int:complaint_id>', methods=['POST'])
@admin_required
def delete_complaint(complaint_id):
    """Delete complaint"""
    try:
        complaint = Complaint.query.get_or_404(complaint_id)
        
        # Store complaint details for notification before deletion
        student_id = complaint.student_id
        complaint_category = complaint.category
        complaint_description = complaint.description
        complaint_status = complaint.status
        
        # Send Telegram notification to student before deletion
        try:
            from app.services.complaint_notification_service import ComplaintNotificationService
            from app.models import Student
            
            student = Student.query.get(student_id)
            if student:
                # Pass complaint details since we're deleting the complaint
                complaint_details = {
                    'category': complaint_category,
                    'description': complaint_description
                }
                ComplaintNotificationService.notify_student_telegram(
                    complaint_id=complaint_id,
                    old_status=complaint_status,
                    new_status="DELETED",
                    student_id=student_id,
                    complaint_details=complaint_details
                )
        except Exception as e:
            current_app.logger.error(f"Error sending deletion notification: {str(e)}")
        
        db.session.delete(complaint)
        db.session.commit()
        
        flash('✅ Complaint deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting complaint: {str(e)}")
        flash(f'❌ Error deleting complaint: {str(e)}', 'error')
    
    return redirect(url_for('admin.manage_complaints'))


@admin_bp.route('/view-notifications')
@login_required
def view_notifications():
    """View all notifications"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        # Get notifications with pagination
        notifications_pagination = safe_execute(
            lambda: Notification.query.order_by(Notification.created_at.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )
        
        notifications = notifications_pagination.items if notifications_pagination else []
        
        return render_template('notifications.html',
                             notifications=notifications,
                             pagination=notifications_pagination,
                             page=page)
    
    except Exception as e:
        current_app.logger.error(f"Error viewing notifications: {str(e)}")
        flash('Error loading notifications.', 'error')
        return render_template('view_notifications.html',
                             notifications=[],
                             pagination=None,
                             page=1)


@admin_bp.route('/notification/<int:notification_id>/details', methods=['GET'])
@login_required
def notification_details(notification_id):
    """Get notification details as JSON"""
    try:
        notification = safe_execute(
            lambda: Notification.query.get_or_404(notification_id)
        )
        
        if notification:
            return jsonify({
                'success': True,
                'notification': {
                    'id': notification.id,
                    'title': notification.title,
                    'content': notification.content,
                    'notification_type': notification.notification_type,
                    'priority': notification.priority,
                    'created_at': notification.created_at.strftime('%d %b %Y, %I:%M %p') if notification.created_at else 'N/A',
                    'expires_at': notification.expires_at.strftime('%d %b %Y, %I:%M %p') if notification.expires_at else 'N/A',
                    'is_expired': notification.is_expired(),
                    'file_url': notification.file_url,
                    'link_url': notification.link_url
                }
            })
        else:
            return jsonify({'success': False, 'message': 'Notification not found'}), 404
    
    except Exception as e:
        current_app.logger.error(f"Error getting notification details: {str(e)}")
        return jsonify({'success': False, 'message': 'Error loading notification details'}), 500


@admin_bp.route('/notification/<int:notification_id>/delete', methods=['POST', 'DELETE'])
@admin_required
def delete_notification(notification_id):
    """Delete a notification"""
    # Handle both POST (from form) and DELETE (from AJAX) methods
    try:
        notification = safe_execute(
            lambda: Notification.query.get_or_404(notification_id)
        )
        
        if notification:
            db.session.delete(notification)
            db.session.commit()
            
            # Check if this is an AJAX request
            if request.method == 'DELETE' or request.headers.get('Content-Type') == 'application/json':
                return jsonify({
                    'success': True,
                    'message': 'Notification deleted successfully'
                })
            else:
                # This is a form submission, redirect back to notifications
                flash('✅ Notification deleted successfully!', 'success')
                return redirect(url_for('admin.view_notifications'))
        else:
            if request.method == 'DELETE' or request.headers.get('Content-Type') == 'application/json':
                return jsonify({'success': False, 'message': 'Notification not found'}), 404
            else:
                flash('❌ Notification not found', 'error')
                return redirect(url_for('admin.view_notifications'))
    
    except Exception as e:
        current_app.logger.error(f"Error deleting notification: {str(e)}")
        db.session.rollback()
        
        if request.method == 'DELETE' or request.headers.get('Content-Type') == 'application/json':
            return jsonify({'success': False, 'message': 'Error deleting notification'}), 500
        else:
            flash('❌ Error deleting notification', 'error')
            return redirect(url_for('admin.view_notifications'))


@admin_bp.route('/edit-notification/<int:notification_id>', methods=['GET', 'POST'])
@admin_required
def edit_notification(notification_id):
    """Edit existing notification"""
    try:
        notification = safe_execute(
            lambda: Notification.query.get_or_404(notification_id)
        )
        
        if request.method == 'POST':
            try:
                notification.title = request.form.get('title')
                notification.content = request.form.get('content')
                notification.file_url = request.form.get('file_url')
                notification.link_url = request.form.get('link_url')
                notification.notification_type = request.form.get('notification_type', 'general')
                notification.priority = request.form.get('priority', 'medium')
                
                # Update timestamp to show it was recently modified
                notification.created_at = datetime.utcnow()
                
                # Handle expires_at
                expires_at = request.form.get('expires_at')
                if expires_at:
                    try:
                        from datetime import datetime
                        notification.expires_at = datetime.strptime(expires_at, '%Y-%m-%dT%H:%M')
                    except ValueError:
                        notification.expires_at = datetime.utcnow() + timedelta(days=7)
                else:
                    notification.expires_at = datetime.utcnow() + timedelta(days=7)
                
                db.session.commit()
                flash('✅ Notification updated successfully!', 'success')
                return redirect(url_for('admin.view_notifications'))
            
            except Exception as e:
                current_app.logger.error(f"Error updating notification: {str(e)}")
                flash(f'❌ Error updating notification: {str(e)}', 'error')
        
        return render_template('edit_notification.html', notification=notification)
    
    except Exception as e:
        current_app.logger.error(f"Error loading notification for edit: {str(e)}")
        flash('Error loading notification.', 'error')
        return redirect(url_for('admin.view_notifications'))


def _get_bot_status():
    """Get real bot status by checking process and Telegram API"""
    try:
        import psutil
        import time
        from app.services.telegram_service import TelegramBotService
        
        bot_token = current_app.config.get('TELEGRAM_BOT_TOKEN', '').strip()
        
        if not bot_token:
            return {
                'status': 'inactive',
                'message': 'TELEGRAM_BOT_TOKEN not configured',
                'last_checked': datetime.utcnow().strftime('%d %b %Y, %I:%M %p')
            }
        
        # Check if bot process is actually running
        bot_process_running = False
        bot_process_info = None
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent', 'create_time']):
            try:
                if proc.info['name'] in ['python', 'python.exe']:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'run_telegram_bot_polling.py' in cmdline:
                        bot_process_running = True
                        uptime = time.time() - proc.info['create_time'] if proc.info.get('create_time') else 0
                        bot_process_info = {
                            'pid': proc.info['pid'],
                            'cpu_usage': round(proc.info['cpu_percent'], 2),
                            'memory_usage': round(proc.info['memory_percent'], 2),
                            'uptime': round(uptime, 2)
                        }
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Check Telegram API connectivity
        telegram_service = TelegramBotService()
        telegram_service.bot_token = bot_token
        bot_info = telegram_service.get_bot_info()
        
        # Determine overall status
        if bot_process_running and bot_info:
            return {
                'status': 'active',
                'message': 'Bot is running and responding',
                'last_checked': datetime.utcnow().strftime('%d %b %Y, %I:%M %p'),
                'process_info': bot_process_info,
                'bot_info': {
                    'username': bot_info.get('username'),
                    'first_name': bot_info.get('first_name'),
                    'can_receive_messages': bot_info.get('can_read_all_group_messages', False)
                }
            }
        elif bot_process_running and not bot_info:
            return {
                'status': 'error',
                'message': 'Bot process running but Telegram API not accessible',
                'last_checked': datetime.utcnow().strftime('%d %b %Y, %I:%M %p'),
                'process_info': bot_process_info
            }
        elif not bot_process_running and bot_info:
            return {
                'status': 'inactive',
                'message': 'Bot is accessible but process not running',
                'last_checked': datetime.utcnow().strftime('%d %b %Y, %I:%M %p'),
                'bot_info': {
                    'username': bot_info.get('username'),
                    'first_name': bot_info.get('first_name')
                }
            }
        else:
            return {
                'status': 'inactive',
                'message': 'Bot is not running',
                'last_checked': datetime.utcnow().strftime('%d %b %Y, %I:%M %p')
            }
            
    except Exception as e:
        current_app.logger.error(f"Bot status check error: {str(e)}")
        return {
            'status': 'error',
            'message': f'Error checking bot status: {str(e)}',
            'last_checked': datetime.utcnow().strftime('%d %b %Y, %I:%M %p')
        }


def _get_recent_activities():
    """Get recent activities from database"""
    try:
        activities = []
        
        # Get recent student registrations
        recent_students = safe_execute(
            lambda: Student.query.order_by(Student.created_at.desc()).limit(3).all()
        ) or []
        
        for student in recent_students:
            activities.append({
                'type': 'student_registration',
                'text': f'New student registered: {student.name} ({student.roll_number})',
                'time': student.created_at.strftime('%d %b %Y, %I:%M %p') if student.created_at else 'N/A',
                'icon': 'user-plus',
                'color': 'success'
            })
        
        # Get recent notifications
        recent_notifications = safe_execute(
            lambda: Notification.query.order_by(Notification.created_at.desc()).limit(3).all()
        ) or []
        
        for notif in recent_notifications:
            activities.append({
                'type': 'notification',
                'text': f'Notification sent: {notif.title}',
                'time': notif.created_at.strftime('%d %b %Y, %I:%M %p') if notif.created_at else 'N/A',
                'icon': 'bullhorn',
                'color': 'info'
            })
        
        # Get recent complaints
        recent_complaints = safe_execute(
            lambda: Complaint.query.order_by(Complaint.created_at.desc()).limit(2).all()
        ) or []
        
        for complaint in recent_complaints:
            activities.append({
                'type': 'complaint',
                'text': f'New complaint filed: {complaint.category}',
                'time': complaint.created_at.strftime('%d %b %Y, %I:%M %p') if complaint.created_at else 'N/A',
                'icon': 'exclamation-triangle',
                'color': 'warning'
            })
        
        # Sort by time and return latest 5
        activities.sort(key=lambda x: x['time'], reverse=True)
        return activities[:5]
        
    except Exception as e:
        current_app.logger.error(f"Recent activities error: {str(e)}")
        return []


# Student Registration Routes
@admin_bp.route('/student-registrations')
@login_required
@admin_required
def student_registrations():
    """View pending student registrations"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        # Get pending registrations
        registrations_pagination = safe_execute(
            lambda: StudentRegistration.query.filter_by(status='pending')
            .order_by(StudentRegistration.registration_date.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )
        
        registrations = registrations_pagination.items if registrations_pagination else []
        
        return render_template('student_registrations.html',
                             registrations=registrations,
                             pagination=registrations_pagination,
                             page=page)
    
    except Exception as e:
        current_app.logger.error(f"Error loading student registrations: {str(e)}")
        flash('Error loading student registrations.', 'error')
        return render_template('student_registrations.html',
                             registrations=[],
                             pagination=None,
                             page=1)


@admin_bp.route('/registration/<int:registration_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_registration(registration_id):
    """Approve student registration"""
    try:
        registration = safe_execute(
            lambda: StudentRegistration.query.get_or_404(registration_id)
        )
        
        if registration.status != 'pending':
            flash('Registration has already been processed.', 'warning')
            return redirect(url_for('admin.student_registrations'))
        
        success, result = registration.approve(current_user.id)
        
        if success:
            flash(f'✅ Registration approved for {registration.name} ({registration.roll_number})', 'success')
        else:
            flash(f'❌ Error approving registration: {result}', 'error')
        
        return redirect(url_for('admin.student_registrations'))
    
    except Exception as e:
        current_app.logger.error(f"Error approving registration: {str(e)}")
        flash('Error approving registration.', 'error')
        return redirect(url_for('admin.student_registrations'))


@admin_bp.route('/registration/<int:registration_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_registration(registration_id):
    """Reject student registration"""
    try:
        registration = safe_execute(
            lambda: StudentRegistration.query.get_or_404(registration_id)
        )
        
        if registration.status != 'pending':
            flash('Registration has already been processed.', 'warning')
            return redirect(url_for('admin.student_registrations'))
        
        registration.reject(current_user.id)
        flash(f'❌ Registration rejected for {registration.name} ({registration.roll_number})', 'info')
        
        return redirect(url_for('admin.student_registrations'))
    
    except Exception as e:
        current_app.logger.error(f"Error rejecting registration: {str(e)}")
        flash('Error rejecting registration.', 'error')
        return redirect(url_for('admin.student_registrations'))


@admin_bp.route('/add-registration', methods=['GET', 'POST'])
@login_required
@admin_required
def add_registration():
    """Add new student registration"""
    if request.method == 'POST':
        try:
            # Check if roll number already exists in students or registrations
            existing_student = safe_execute(
                lambda: Student.query.filter_by(roll_number=request.form['roll_number']).first()
            )
            existing_registration = safe_execute(
                lambda: StudentRegistration.query.filter_by(roll_number=request.form['roll_number']).first()
            )
            
            if existing_student or existing_registration:
                flash('Roll number already exists!', 'error')
                return render_template('add_registration.html')
            
            # Create new registration
            registration = StudentRegistration(
                roll_number=request.form['roll_number'],
                name=request.form['name'],
                phone=request.form['phone'],
                email=request.form.get('email', ''),
                department=request.form.get('department', ''),
                semester=int(request.form.get('semester', 1)) if request.form.get('semester') else None
            )
            
            db.session.add(registration)
            db.session.commit()
            
            flash('✅ Student registration added successfully! Awaiting approval.', 'success')
            return redirect(url_for('admin.student_registrations'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding registration: {str(e)}")
            flash('Error adding registration.', 'error')
    
    return render_template('add_registration.html')

@admin_bp.route('/bot-status')
@login_required
@admin_required
def bot_status():
    """Get real-time bot status for admin dashboard"""
    try:
        import subprocess
        import psutil
        import time
        from datetime import datetime
        
        # Check if bot process is running
        bot_running = False
        bot_info = {
            'status': 'offline',
            'message': 'Bot is not running',
            'last_check': datetime.utcnow().isoformat(),
            'uptime': None,
            'memory_usage': None,
            'cpu_usage': None
        }
        
        # Check for python processes that might be the bot (same logic as toggle endpoint)
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent', 'create_time']):
            try:
                if proc.info['name'] in ['python', 'python.exe']:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    # Check for the main bot script (student/visitor polling mode)
                    if 'run_telegram_bot_polling.py' in cmdline:
                        bot_running = True
                        uptime = time.time() - proc.info['create_time'] if proc.info.get('create_time') else 0
                        
                        bot_type = 'Student/Visitor Bot (Polling)'
                        
                        bot_info.update({
                            'status': 'online',
                            'message': f'Bot is running ({bot_type} mode)',
                            'pid': proc.info['pid'],
                            'cpu_usage': round(proc.info['cpu_percent'], 2),
                            'memory_usage': round(proc.info['memory_percent'], 2),
                            'uptime': round(uptime, 2),
                            'cmdline': cmdline[:100] + '...' if len(cmdline) > 100 else cmdline
                        })
                        current_app.logger.info(f"Bot process found: PID {proc.info['pid']} ({bot_type})")
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # No fallback health check - rely only on actual process detection
        
        # Check database connectivity as another indicator
        try:
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            bot_info['database_status'] = 'connected'
        except Exception as e:
            bot_info['database_status'] = 'error'
            bot_info['database_error'] = str(e)
        
        current_app.logger.info(f"Bot status check: {bot_info['status']} - {bot_info['message']}")
        return jsonify(bot_info)
        
    except Exception as e:
        current_app.logger.error(f"Error checking bot status: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error checking bot status: {str(e)}',
            'last_check': datetime.utcnow().isoformat()
        }), 500

@admin_bp.route('/toggle-bot', methods=['POST'])
@login_required
@admin_required
def toggle_bot():
    """Toggle bot activation/deactivation with improved reliability"""
    try:
        import subprocess
        import os
        import signal
        import psutil
        import threading
        import time
        from datetime import datetime
        
        data = request.get_json()
        action = data.get('action', 'activate')
        
        current_app.logger.info(f"Bot toggle request: {action} by user: {current_user.username}")
        
        if action == 'activate':
            # Check if bot is already running (same logic as status function)
            bot_already_running = False
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['name'] in ['python', 'python.exe']:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    # Prioritize the main bot script (student/visitor polling mode)
                    if 'run_telegram_bot_polling.py' in cmdline:
                        bot_already_running = True
                        current_app.logger.info(f"Bot already running with PID: {proc.info['pid']}")
                        break
            
            if bot_already_running:
                return jsonify({
                    'success': False,
                    'message': 'Bot is already running',
                    'status': 'online'
                })
            
            # Try the main bot script (student/visitor polling mode)
            bot_script = 'run_telegram_bot_polling.py'
            bot_script_path = os.path.join(os.getcwd(), 'scripts', 'bot', bot_script)
            
            if not os.path.exists(bot_script_path):
                return jsonify({
                    'success': False,
                    'message': f'Bot script not found: {bot_script}',
                    'status': 'error'
                })
            
            current_app.logger.info(f"Using bot script: {bot_script_path}")
            
            # Start bot with improved error handling
            def start_bot_process():
                try:
                    env = os.environ.copy()
                    env['PYTHONPATH'] = os.getcwd()
                    
                    # Check if TELEGRAM_BOT_TOKEN is available
                    if not current_app.config.get('TELEGRAM_BOT_TOKEN'):
                        return {'success': False, 'error': 'TELEGRAM_BOT_TOKEN not configured'}
                    
                    # Send activation notification to admin
                    admin_chat_id = os.environ.get('ADMIN_TELEGRAM_CHAT_ID')
                    if admin_chat_id:
                        try:
                            import requests
                            bot_token = current_app.config.get('TELEGRAM_BOT_TOKEN')
                            message = f"🤖 *Bot Activated*\n\n👤 Admin: {current_user.username}\n🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n🔄 Mode: Polling\n\n✅ EduBot is now online and ready to assist!"
                            
                            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                            data = {
                                'chat_id': admin_chat_id,
                                'text': message,
                                'parse_mode': 'Markdown'
                            }
                            requests.post(url, json=data, timeout=10)
                            current_app.logger.info(f"Activation notification sent to admin chat {admin_chat_id}")
                        except Exception as e:
                            current_app.logger.warning(f"Failed to send activation notification: {str(e)}")
                    
                    # Use subprocess with better error handling (no PIPE to prevent hanging)
                    process = subprocess.Popen([
                        'python', bot_script_path
                    ], 
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    cwd=os.getcwd(),
                    env=env,
                    text=True,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
                    )
                    
                    # Wait a moment to check if it starts successfully
                    time.sleep(2)
                    
                    if process.poll() is None:
                        current_app.logger.info(f"Bot started successfully with PID: {process.pid}")
                        return {'success': True, 'pid': process.pid, 'process': process}
                    else:
                        exit_code = process.poll()
                        current_app.logger.error(f"Bot failed to start. Exit code: {exit_code}")
                        return {'success': False, 'error': f'Bot process exited with code {exit_code}'}
                        
                except Exception as e:
                    current_app.logger.error(f"Exception starting bot: {str(e)}")
                    return {'success': False, 'error': str(e)}
            
            # Start bot directly (no threading to avoid issues)
            result = start_bot_process()
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'message': f'Bot started successfully with PID {result["pid"]}',
                    'status': 'online'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': f'Failed to start bot: {result["error"]}',
                    'status': 'error'
                })
                
        elif action == 'deactivate':
            # Stop the bot with improved process detection
            stopped_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['name'] in ['python', 'python.exe']:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    # More specific matching to avoid killing other Python processes
                    if any(script in cmdline for script in ['run_telegram_bot_simple.py', 'run_telegram_bot_polling.py', 'run_telegram_bot.py', 'activate_telegram_bot.py', 'simple_telegram_bot.py']):
                        try:
                            # Try graceful termination first
                            proc.terminate()
                            stopped_processes.append(proc.info['pid'])
                            current_app.logger.info(f"Terminated bot process {proc.info['pid']}")
                            
                            # Wait a moment for graceful termination
                            time.sleep(0.5)
                            
                            # Check if process is still running and force kill if needed
                            if proc.is_running():
                                proc.kill()
                                current_app.logger.info(f"Force killed bot process {proc.info['pid']}")
                                
                        except psutil.NoSuchProcess:
                            continue
                        except psutil.AccessDenied:
                            try:
                                os.kill(proc.info['pid'], signal.SIGTERM)
                                stopped_processes.append(proc.info['pid'])
                                current_app.logger.info(f"SIGTERM sent to process {proc.info['pid']}")
                            except:
                                continue
            
            if stopped_processes:
                current_app.logger.info(f"Stopped {len(stopped_processes)} bot processes")
                
                # Send deactivation notification to admin
                admin_chat_id = os.environ.get('ADMIN_TELEGRAM_CHAT_ID')
                if admin_chat_id:
                    try:
                        import requests
                        bot_token = current_app.config.get('TELEGRAM_BOT_TOKEN')
                        message = f"🛑 *Bot Deactivated*\n\n👤 Admin: {current_user.username}\n🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n🔄 Processes Stopped: {len(stopped_processes)}\n\n⚠️ EduBot is now offline and will not respond to messages."
                        
                        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                        data = {
                            'chat_id': admin_chat_id,
                            'text': message,
                            'parse_mode': 'Markdown'
                        }
                        requests.post(url, json=data, timeout=10)
                        current_app.logger.info(f"Deactivation notification sent to admin chat {admin_chat_id}")
                    except Exception as e:
                        current_app.logger.warning(f"Failed to send deactivation notification: {str(e)}")
                
                return jsonify({
                    'success': True,
                    'message': f'Bot stopped successfully. Terminated {len(stopped_processes)} process(es).',
                    'status': 'offline',
                    'stopped_processes': stopped_processes
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'No running bot processes found',
                    'status': 'offline'
                })
        
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid action specified. Use "activate" or "deactivate"',
                'status': 'error'
            })
            
    except Exception as e:
        current_app.logger.error(f"Error in toggle_bot: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error toggling bot: {str(e)}',
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# Predefined Info Management Routes
@admin_bp.route('/predefined-info')
@admin_required
def predefined_info():
    """Manage predefined college information"""
    try:
        # Get statistics
        total_info = PredefinedInfo.query.count()
        active_info = PredefinedInfo.query.filter_by(is_active=True).count()
        
        # Group by sections
        sections = db.session.query(
            PredefinedInfo.section,
            db.func.count(PredefinedInfo.id).label('count')
        ).group_by(PredefinedInfo.section).all()
        
        # Get recent updates
        recent_info = PredefinedInfo.query.order_by(PredefinedInfo.updated_at.desc()).limit(5).all()
        
        return render_template('predefined_info.html',
                             total_info=total_info,
                             active_info=active_info,
                             sections=sections,
                             recent_info=recent_info)
    
    except Exception as e:
        current_app.logger.error(f"Error loading predefined info: {str(e)}")
        flash('Error loading predefined information.', 'error')
        return redirect(url_for('admin.admin_dashboard_main'))

@admin_bp.route('/manage-predefined-info')
@admin_required
def manage_predefined_info():
    """Manage predefined information"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        section = request.args.get('section', '')
        search = request.args.get('search', '')
        
        # Build query
        query = PredefinedInfo.query
        
        if section:
            query = query.filter_by(section=section)
        
        if search:
            query = query.filter(
                PredefinedInfo.title.contains(search) |
                PredefinedInfo.content.contains(search)
            )
        
        # Paginate
        info_pagination = query.order_by(PredefinedInfo.section, PredefinedInfo.title).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Get sections for filter
        sections = db.session.query(PredefinedInfo.section).distinct().all()
        
        return render_template('manage_predefined_info.html',
                             info_pagination=info_pagination,
                             sections=sections,
                             selected_section=section,
                             search=search)
    
    except Exception as e:
        current_app.logger.error(f"Error loading manage predefined info: {str(e)}")
        flash('Error loading predefined information.', 'error')
        return redirect(url_for('admin.predefined_info'))

@admin_bp.route('/add-predefined-info', methods=['GET', 'POST'])
@admin_required
def add_predefined_info():
    """Add new predefined information"""
    if request.method == 'POST':
        try:
            info = PredefinedInfo(
                section=request.form.get('section'),
                title=request.form.get('title'),
                content=request.form.get('content'),
                category=request.form.get('category'),
                is_active='is_active' in request.form,
                updated_by=current_user.id
            )
            
            db.session.add(info)
            db.session.commit()
            
            flash('✅ Predefined information added successfully!', 'success')
            return redirect(url_for('admin.manage_predefined_info'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding predefined info: {str(e)}")
            flash(f'❌ Error adding predefined information: {str(e)}', 'error')
    
    return render_template('add_predefined_info.html')

@admin_bp.route('/edit-predefined-info/<int:info_id>', methods=['GET', 'POST'])
@admin_required
def edit_predefined_info(info_id):
    """Edit predefined information"""
    info = PredefinedInfo.query.get_or_404(info_id)
    
    if request.method == 'POST':
        try:
            info.section = request.form.get('section')
            info.title = request.form.get('title')
            info.content = request.form.get('content')
            info.category = request.form.get('category')
            info.is_active = 'is_active' in request.form
            info.updated_by = current_user.id
            info.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            flash('✅ Predefined information updated successfully!', 'success')
            return redirect(url_for('admin.manage_predefined_info'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating predefined info: {str(e)}")
            flash(f'❌ Error updating predefined information: {str(e)}', 'error')
    
    return render_template('edit_predefined_info.html', info=info)

@admin_bp.route('/delete-predefined-info/<int:info_id>', methods=['POST'])
@admin_required
def delete_predefined_info(info_id):
    """Delete predefined information"""
    try:
        info = PredefinedInfo.query.get_or_404(info_id)
        db.session.delete(info)
        db.session.commit()
        
        flash('✅ Predefined information deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting predefined info: {str(e)}")
        flash(f'❌ Error deleting predefined information: {str(e)}', 'error')
    
    return redirect(url_for('admin.manage_predefined_info'))

# FAQ Records Management Routes (Real-time Data Processing)
@admin_bp.route('/faq-records')
@admin_required
def faq_records():
    """Manage FAQ Records - Questions from visitors/students"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        show_processed = request.args.get('show_processed', 'false') == 'true'
        
        # Build query using real FAQ records
        query = db.session.query(FAQRecord)
        
        if not show_processed:
            query = query.filter_by(processed=False)
        
        # Paginate
        records_pagination = query.order_by(FAQRecord.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('faq_records.html',
                             records_pagination=records_pagination,
                             show_processed=show_processed)
    
    except Exception as e:
        current_app.logger.error(f"Error loading FAQ records: {str(e)}")
        flash('Error loading FAQ records.', 'error')
        return redirect(url_for('admin.faq_management'))

@admin_bp.route('/process-faq-record/<int:record_id>', methods=['GET', 'POST'])
@admin_required
def process_faq_record(record_id):
    """Process FAQ record and convert to FAQ"""
    record = db.session.query(FAQRecord).get_or_404(record_id)
    
    if request.method == 'POST':
        try:
            # Check if this query has been asked frequently (count > 20)
            query_count = db.session.query(FAQRecord).filter(
                FAQRecord.query.ilike(f'%{record.query}%')
            ).count()
            
            if query_count < 20:
                flash('⚠️ This query has been asked less than 20 times. It will be added to regular Q&A instead of FAQ.', 'warning')
                # Add to regular ChatbotQA
                new_query = ChatbotQA(
                    question=record.query,
                    answer=request.form.get('answer'),
                    category=request.form.get('category')
                )
            else:
                # Add to FAQ (high frequency)
                new_faq = FAQ(
                    question=record.query,
                    answer=request.form.get('answer'),
                    category=request.form.get('category'),
                    priority=int(request.form.get('priority', 2)),  # default medium priority
                    updated_by=current_user.id
                )
                record.faq_id = new_faq.id  # Link record to created FAQ
                db.session.add(new_faq)
            
            # Mark record as processed
            record.processed = True
            
            db.session.add(new_query if query_count < 20 else new_faq)
            db.session.commit()
            
            flash(f'✅ FAQ record processed successfully! (Asked {query_count} times)', 'success')
            return redirect(url_for('admin.faq_records'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error processing FAQ record: {str(e)}")
            flash(f'❌ Error processing FAQ record: {str(e)}', 'error')
    
    return render_template('process_faq_record.html', record=record)

@admin_bp.route('/delete-faq-record/<int:record_id>', methods=['POST'])
@admin_required
def delete_faq_record(record_id):
    """Delete FAQ record"""
    try:
        record = db.session.query(FAQRecord).get_or_404(record_id)
        db.session.delete(record)
        db.session.commit()
        
        flash('✅ FAQ record deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting FAQ record: {str(e)}")
        flash(f'❌ Error deleting FAQ record: {str(e)}', 'error')
    
    return redirect(url_for('admin.faq_records'))

# Update FAQ Management to show real-time data
@admin_bp.route('/faq-management')
@admin_required
def faq_management():
    """Manage frequently asked questions - Real-time data"""
    try:
        # Get real-time statistics
        total_faqs = FAQ.query.count()
        active_faqs = FAQ.query.filter_by(is_active=True).count()
        high_priority_faqs = FAQ.query.filter_by(priority=3).count()
        
        # Get real FAQ records count
        total_records = db.session.query(FAQRecord).count()
        unprocessed_records = db.session.query(FAQRecord).filter_by(processed=False).count()
        
        # Get categories from real FAQs
        categories = db.session.query(
            FAQ.category,
            db.func.count(FAQ.id).label('count')
        ).group_by(FAQ.category).all()
        
        # Get popular FAQs (high view count)
        popular_faqs = FAQ.query.order_by(FAQ.view_count.desc()).limit(5).all()
        
        # Get recent FAQ records
        recent_records = db.session.query(FAQRecord).order_by(FAQRecord.created_at.desc()).limit(5).all()
        
        return render_template('faq_management.html',
                             total_faqs=total_faqs,
                             active_faqs=active_faqs,
                             high_priority_faqs=high_priority_faqs,
                             total_records=total_records,
                             unprocessed_records=unprocessed_records,
                             categories=categories,
                             popular_faqs=popular_faqs,
                             recent_records=recent_records)
    
    except Exception as e:
        current_app.logger.error(f"Error loading FAQ management: {str(e)}")
        flash('Error loading FAQ management.', 'error')
        return redirect(url_for('admin.admin_dashboard_main'))

@admin_bp.route('/manage-faqs')
@admin_required
def manage_faqs():
    """Manage FAQs"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        category = request.args.get('category', '')
        priority = request.args.get('priority', '')
        search = request.args.get('search', '')
        
        # Build query
        query = FAQ.query
        
        if category:
            query = query.filter_by(category=category)
        
        if priority:
            query = query.filter_by(priority=int(priority))
        
        if search:
            query = query.filter(
                FAQ.question.contains(search) |
                FAQ.answer.contains(search)
            )
        
        # Paginate
        faq_pagination = query.order_by(FAQ.priority.desc(), FAQ.question).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Get categories and priorities for filter
        categories = db.session.query(FAQ.category).distinct().all()
        
        return render_template('manage_faqs.html',
                             faq_pagination=faq_pagination,
                             categories=categories,
                             selected_category=category,
                             selected_priority=priority,
                             search=search)
    
    except Exception as e:
        current_app.logger.error(f"Error loading manage FAQs: {str(e)}")
        flash('Error loading FAQs.', 'error')
        return redirect(url_for('admin.faq_management'))

@admin_bp.route('/add-faq', methods=['GET', 'POST'])
@admin_required
def add_faq():
    """Add new FAQ"""
    if request.method == 'POST':
        try:
            faq = FAQ(
                question=request.form.get('question'),
                answer=request.form.get('answer'),
                category=request.form.get('category'),
                priority=int(request.form.get('priority', 1)),
                is_active='is_active' in request.form,
                updated_by=current_user.id
            )
            
            db.session.add(faq)
            db.session.commit()
            
            flash('✅ FAQ added successfully!', 'success')
            return redirect(url_for('admin.manage_faqs'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding FAQ: {str(e)}")
            flash(f'❌ Error adding FAQ: {str(e)}', 'error')
    
    return render_template('add_faq.html')

@admin_bp.route('/edit-faq/<int:faq_id>', methods=['GET', 'POST'])
@admin_required
def edit_faq(faq_id):
    """Edit FAQ"""
    faq = FAQ.query.get_or_404(faq_id)
    
    if request.method == 'POST':
        try:
            faq.question = request.form.get('question')
            faq.answer = request.form.get('answer')
            faq.category = request.form.get('category')
            faq.priority = int(request.form.get('priority', 1))
            faq.is_active = 'is_active' in request.form
            faq.updated_by = current_user.id
            faq.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            flash('✅ FAQ updated successfully!', 'success')
            return redirect(url_for('admin.manage_faqs'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating FAQ: {str(e)}")
            flash(f'❌ Error updating FAQ: {str(e)}', 'error')
    
    return render_template('edit_faq.html', faq=faq)

@admin_bp.route('/delete-faq/<int:faq_id>', methods=['POST'])
@admin_required
def delete_faq(faq_id):
    """Delete FAQ"""
    try:
        faq = FAQ.query.get_or_404(faq_id)
        db.session.delete(faq)
        db.session.commit()
        
        flash('✅ FAQ deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting FAQ: {str(e)}")
        flash(f'❌ Error deleting FAQ: {str(e)}', 'error')
    
    return redirect(url_for('admin.manage_faqs'))

# Real-time Activity Refresh Route
@admin_bp.route('/refresh-activity', methods=['POST'])
@admin_required
def refresh_activity():
    """Refresh recent activity with real-time data"""
    try:
        from datetime import datetime, timedelta
        
        activities = []
        
        # Get real recent notifications (last 24 hours)
        recent_notifications = Notification.query.filter(
            Notification.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).order_by(Notification.created_at.desc()).limit(5).all()
        
        for notification in recent_notifications:
            activities.append({
                'text': f"New notification: {notification.title}",
                'time': format_time_ago(notification.created_at),
                'icon': 'bullhorn',
                'color': 'info'
            })
        
        # Get real recent student registrations (last 24 hours)
        recent_registrations = StudentRegistration.query.filter(
            StudentRegistration.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).order_by(StudentRegistration.created_at.desc()).limit(3).all()
        
        for registration in recent_registrations:
            activities.append({
                'text': f"New student registration: {registration.name} ({registration.roll_number})",
                'time': format_time_ago(registration.created_at),
                'icon': 'user-plus',
                'color': 'success'
            })
        
        # Get real recent complaints (last 24 hours)
        recent_complaints = Complaint.query.filter(
            Complaint.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).order_by(Complaint.created_at.desc()).limit(3).all()
        
        for complaint in recent_complaints:
            activities.append({
                'text': f"New complaint registered: {complaint.category.title()}",
                'time': format_time_ago(complaint.created_at),
                'icon': 'exclamation-triangle',
                'color': 'warning'
            })
        
        # Get real recent FAQ records (last 24 hours)
        recent_faq_records = db.session.query(FAQRecord).filter(
            FAQRecord.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).order_by(FAQRecord.created_at.desc()).limit(3).all()
        
        for record in recent_faq_records:
            activities.append({
                'text': f"New FAQ record: {record.query[:50]}...",
                'time': format_time_ago(record.created_at),
                'icon': 'question',
                'color': 'primary'
            })
        
        # Get real recent predefined info updates (last 24 hours)
        recent_info_updates = PredefinedInfo.query.filter(
            PredefinedInfo.updated_at >= datetime.utcnow() - timedelta(hours=24)
        ).order_by(PredefinedInfo.updated_at.desc()).limit(3).all()
        
        for info in recent_info_updates:
            activities.append({
                'text': f"Updated {info.section.title()}: {info.title}",
                'time': format_time_ago(info.updated_at),
                'icon': 'edit',
                'color': 'secondary'
            })
        
        # Sort all activities by time (most recent first)
        # Put 'N/A' values at the end
        activities_with_time = [a for a in activities if a['time'] != 'N/A']
        activities_with_na = [a for a in activities if a['time'] == 'N/A']
        
        activities_with_time.sort(key=lambda x: x['time'], reverse=True)
        activities = activities_with_time + activities_with_na
        
        # Limit to 10 most recent activities
        activities = activities[:10]
        
        return jsonify({
            'success': True,
            'activities': activities,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error refreshing activity: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error refreshing activity',
            'activities': []
        }), 500

def format_time_ago(dt):
    """Format datetime as 'X hours/minutes ago'"""
    if dt is None:
        return 'N/A'
    
    from datetime import datetime
    now = datetime.utcnow()
    diff = now - dt
    
    if diff < timedelta(minutes=1):
        return "Just now"
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
                
            except Exception as e:
                current_app.logger.error(f"Error sending email: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': f'Report generated but email failed: {str(e)}',
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
