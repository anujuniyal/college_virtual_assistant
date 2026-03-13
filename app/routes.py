"""
Application Routes
"""
from datetime import datetime
import os

from flask import (
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for,
    flash,
    current_app
)
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import (
    Admin, Student, Faculty, Notification, 
    Result, FeeRecord, Complaint, ChatbotQA, FAQRecord
)
from app.chatbot.service import ChatbotService

from app.services.otp_service import OTPService
from app.services.complaint_notification_service import ComplaintNotificationService


# Decorators
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def register_routes(app):
    """Register all application routes"""
    """Register all routes"""
    
    @app.route('/')
    def index():
        """Home page"""
        return redirect(url_for('login'))
    
    @app.route('/auth/login', methods=['GET', 'POST'])
    def auth_login_redirect():
        """Redirect old auth/login to new login route"""
        if request.method == 'POST':
            # Handle POST data and process login directly
            username = request.form.get('username')
            password = request.form.get('password')
            
            # First check Admin table
            admin = Admin.query.filter_by(username=username).first()
            
            if admin and admin.check_password(password):
                login_user(admin, remember=True)
                session['user_role'] = admin.role
                session['user_name'] = admin.username
                
                # Redirect based on role
                if admin.role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif admin.role == 'faculty':
                    return redirect(url_for('faculty_dashboard'))
                elif admin.role == 'accounts':
                    return redirect(url_for('accounts_dashboard'))
                else:
                    return redirect(url_for('admin_dashboard'))
            
            # If not found in Admin table, check Faculty table
            faculty = Faculty.query.filter_by(email=username).first()
            
            if faculty and faculty.check_password(password):
                login_user(faculty, remember=True)
                session['user_role'] = faculty.role
                session['user_name'] = faculty.name
                
                # Redirect based on role
                if faculty.role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif faculty.role == 'faculty':
                    return redirect(url_for('faculty_dashboard'))
                elif faculty.role == 'accounts':
                    return redirect(url_for('accounts_dashboard'))
                else:
                    return redirect(url_for('faculty_dashboard'))
            
            # Also check by name if email doesn't work
            faculty_by_name = Faculty.query.filter_by(name=username).first()
            if faculty_by_name and faculty_by_name.check_password(password):
                login_user(faculty_by_name, remember=True)
                session['user_role'] = faculty_by_name.role
                session['user_name'] = faculty_by_name.name
                
                # Redirect based on role
                if faculty_by_name.role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif faculty_by_name.role == 'faculty':
                    return redirect(url_for('faculty_dashboard'))
                elif faculty_by_name.role == 'accounts':
                    return redirect(url_for('accounts_dashboard'))
                else:
                    return redirect(url_for('faculty_dashboard'))
            
            else:
                flash('Invalid username/email or password', 'error')
                return render_template('login.html')
        else:
            # Redirect GET requests
            return redirect(url_for('login'))
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Multi-role login system"""
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            # First check Admin table
            admin = Admin.query.filter_by(username=username).first()
            
            if admin and admin.check_password(password):
                login_user(admin, remember=True)
                session['user_role'] = admin.role
                session['user_name'] = admin.username
                
                # Redirect based on role
                if admin.role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif admin.role == 'faculty':
                    return redirect(url_for('faculty_dashboard'))
                elif admin.role == 'accounts':
                    return redirect(url_for('accounts_dashboard'))
                else:
                    return redirect(url_for('admin_dashboard'))
            
            # If not found in Admin table, check Faculty table
            faculty = Faculty.query.filter_by(email=username).first()
            
            if faculty and faculty.check_password(password):
                login_user(faculty, remember=True)
                session['user_role'] = faculty.role
                session['user_name'] = faculty.name
                
                # Redirect based on role
                if faculty.role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif faculty.role == 'faculty':
                    return redirect(url_for('faculty_dashboard'))
                elif faculty.role == 'accounts':
                    return redirect(url_for('accounts_dashboard'))
                else:
                    return redirect(url_for('faculty_dashboard'))
            
            # Also check by name if email doesn't work
            faculty_by_name = Faculty.query.filter_by(name=username).first()
            if faculty_by_name and faculty_by_name.check_password(password):
                login_user(faculty_by_name, remember=True)
                session['user_role'] = faculty_by_name.role
                session['user_name'] = faculty_by_name.name
                
                # Redirect based on role
                if faculty_by_name.role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif faculty_by_name.role == 'faculty':
                    return redirect(url_for('faculty_dashboard'))
                elif faculty_by_name.role == 'accounts':
                    return redirect(url_for('accounts_dashboard'))
                else:
                    return redirect(url_for('faculty_dashboard'))
            
            else:
                flash('Invalid username/email or password', 'error')
        
        return render_template('login.html')
    
    @app.route('/logout')
    @login_required
    def logout():
        """Logout"""
        logout_user()
        session.clear()
        flash('You have been logged out', 'info')
        return redirect(url_for('login'))
    
    @app.route('/faculty/dashboard')
    @login_required
    def faculty_dashboard():
        """Faculty dashboard"""
        if session.get('user_role') != 'faculty':
            flash('Access denied. Faculty role required.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        # Get faculty-specific data
        total_results = Result.query.count()
        total_students = Student.query.count()
        faculty_info = Faculty.query.filter_by(email=current_user.email).first()
        
        return render_template('faculty_dashboard.html',
                             total_results=total_results,
                             total_students=total_students,
                             faculty_info=faculty_info)
    
    @app.route('/accounts/dashboard')
    @login_required
    def accounts_dashboard():
        """Accounts dashboard"""
        if session.get('user_role') != 'accounts':
            flash('Access denied. Accounts role required.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        # Get accounts-specific data
        total_students = Student.query.count()
        total_fee_records = FeeRecord.query.count()
        total_pending = FeeRecord.query.filter(FeeRecord.balance_amount > 0).count()
        
        # Calculate total pending amount
        pending_amount = db.session.query(db.func.sum(FeeRecord.balance_amount)).filter(FeeRecord.balance_amount > 0).scalar() or 0
        
        # Calculate collection rate
        if total_fee_records > 0:
            collection_rate = round((total_fee_records - total_pending) / total_fee_records * 100, 1)
        else:
            collection_rate = 100.0
        
        return render_template('accounts_dashboard.html',
                             total_students=total_students,
                             total_fee_records=total_fee_records,
                             total_pending=total_pending,
                             pending_amount=pending_amount,
                             collection_rate=collection_rate)
    
    @app.route('/notifications')
    @login_required
    def notifications_dashboard():
        """Notifications dashboard"""
        # Get all notifications with author info
        notifications = db.session.query(Notification, Admin).outerjoin(Admin, Notification.created_by == Admin.id).order_by(Notification.created_at.desc()).all()
        
        return render_template('notifications.html', notifications=notifications)
    
    @app.route('/students')
    @login_required
    def students_dashboard():
        """Students dashboard"""
        if session.get('user_role') not in ['admin', 'faculty']:
            flash('Access denied. Admin or Faculty role required.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        students = Student.query.order_by(Student.created_at.desc()).all()
        return render_template('students.html', students=students)
    
    # CSV Export Routes
    @app.route('/export/students')
    @login_required
    def export_students():
        """Export students to CSV"""
        if session.get('user_role') not in ['admin', 'faculty']:
            flash('Access denied.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        import csv
        import io
        from flask import Response
        
        students = Student.query.all()
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['Roll Number', 'Name', 'Phone', 'Email', 'Department', 'Semester', 'Created At'])
        for student in students:
            writer.writerow([
                student.roll_number, student.name, student.phone,
                student.email, student.department, student.semester,
                student.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=students.csv'}
        )
    
    @app.route('/export/results')
    @login_required
    def export_results():
        """Export results to CSV"""
        if session.get('user_role') not in ['admin', 'faculty']:
            flash('Access denied.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        import csv
        import io
        from flask import Response
        
        results = db.session.query(Result, Student).join(Student).all()
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['Roll Number', 'Student Name', 'Semester', 'Subject', 'Marks', 'Grade', 'Declared At'])
        for result, student in results:
            writer.writerow([
                student.roll_number, student.name, result.semester,
                result.subject, result.marks, result.grade,
                result.declared_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=results.csv'}
        )
    
    @app.route('/export/fee_records')
    @login_required
    def export_fee_records():
        """Export fee records to CSV"""
        if session.get('user_role') not in ['admin', 'accounts']:
            flash('Access denied.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        import csv
        import io
        from flask import Response
        
        fee_records = db.session.query(FeeRecord, Student).join(Student).all()
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['Roll Number', 'Student Name', 'Semester', 'Total Amount', 'Paid Amount', 'Balance', 'Last Updated'])
        for fee, student in fee_records:
            writer.writerow([
                student.roll_number, student.name, fee.semester,
                fee.total_amount, fee.paid_amount, fee.balance_amount,
                fee.last_updated.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=fee_records.csv'}
        )
    
    # File Upload Routes
    @app.route('/upload/notification', methods=['POST'])
    @login_required
    def upload_notification_file():
        """Upload file for notification"""
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('notifications_dashboard'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('notifications_dashboard'))
        
        if file and file.filename.endswith(('.pdf', '.doc', '.docx', '.jpg', '.png')):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash(f'File {filename} uploaded successfully', 'success')
        else:
            flash('Invalid file type', 'error')
        
        return redirect(url_for('notifications_dashboard'))
    
    @app.route('/admin/test-weekly')
    @login_required
    def test_weekly():
        """Test weekly report generation"""
        return "Weekly report test route working!"
    
    @app.route('/admin/add-student', methods=['GET', 'POST'])
    @login_required
    def add_student():
        """Add new student"""
        if session.get('user_role') != 'admin':
            flash('Access denied. Admin role required.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        if request.method == 'POST':
            try:
                student = Student(
                    roll_number=request.form.get('roll_number'),
                    name=request.form.get('name'),
                    phone=request.form.get('phone'),
                    email=request.form.get('email'),
                    department=request.form.get('department'),
                    semester=int(request.form.get('semester', 1))
                )
                db.session.add(student)
                db.session.commit()
                flash('✅ Student added successfully!', 'success')
                return redirect(url_for('students_dashboard'))
            except Exception as e:
                flash(f'❌ Error adding student: {str(e)}', 'error')
        
        return render_template('add_student.html')
    
    @app.route('/admin/add-faculty', methods=['GET', 'POST'])
    @login_required
    def add_faculty():
        """Add new faculty"""
        if session.get('user_role') != 'admin':
            flash('Access denied. Admin role required.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        if request.method == 'POST':
            try:
                faculty = Faculty(
                    name=request.form.get('name'),
                    email=request.form.get('email'),
                    department=request.form.get('department'),
                    consultation_time=request.form.get('consultation_time'),
                    phone=request.form.get('phone')
                )
                db.session.add(faculty)
                db.session.commit()
                flash('✅ Faculty added successfully!', 'success')
                return redirect(url_for('faculty_dashboard'))
            except Exception as e:
                flash(f'❌ Error adding faculty: {str(e)}', 'error')
        
        return render_template('add_faculty.html')
    
    @app.route('/admin/add-notification', methods=['GET', 'POST'])
    @login_required
    def add_notification():
        """Add new notification"""
        if session.get('user_role') != 'admin':
            flash('Access denied. Admin role required.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        if request.method == 'POST':
            try:
                from datetime import datetime, timedelta
                from app.models import Admin
                
                # Get form data
                title = request.form.get('title')
                content = request.form.get('content')
                link_url = request.form.get('link_url')
                link_text = request.form.get('link_text')
                file_url = request.form.get('file_url')
                priority = request.form.get('priority', 'normal')
                expiry_days = int(request.form.get('expiry_days', 7))
                target_audience = request.form.getlist('target_audience')
                
                # Validate required fields
                if not title or not content:
                    flash('Title and content are required fields.', 'error')
                    return render_template('add_notification.html')
                
                # Create notification
                notification = Notification(
                    title=title,
                    content=content,
                    link_url=link_url,
                    file_url=file_url,
                    expires_at=datetime.utcnow() + timedelta(days=expiry_days),
                    created_by=current_user.id
                )
                
                # Add additional metadata in the content or as separate fields
                # For now, we'll store priority and target audience in the content
                # In a real application, you might want to add these as separate columns
                
                db.session.add(notification)
                db.session.commit()
                
                flash('✅ Notification added successfully!', 'success')
                return redirect(url_for('notifications_dashboard'))
                
            except Exception as e:
                flash(f'❌ Error adding notification: {str(e)}', 'error')
        
        return render_template('add_notification.html')
    
    @app.route('/admin/manage-students')
    @login_required
    def manage_students():
        """Manage all students (admin only)"""
        if session.get('user_role') != 'admin':
            flash('Access denied. Admin role required.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        students = Student.query.order_by(Student.created_at.desc()).all()
        return render_template('manage_students.html', students=students)
    
    @app.route('/admin/manage-faculty')
    @login_required
    def manage_faculty():
        """Manage all faculty (admin only)"""
        if session.get('user_role') != 'admin':
            flash('Access denied. Admin role required.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        faculty = Faculty.query.order_by(Faculty.created_at.desc()).all()
        return render_template('manage_faculty.html', faculty=faculty)
    
    @app.route('/admin/manage-accounts')
    @login_required
    def manage_accounts():
        """Manage all accounts (admin only)"""
        if session.get('user_role') != 'admin':
            flash('Access denied. Admin role required.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        accounts = Admin.query.order_by(Admin.created_at.desc()).all()
        return render_template('manage_accounts.html', accounts=accounts)
    
    @app.route('/admin/edit-student/<int:student_id>', methods=['GET', 'POST'])
    @login_required
    def edit_student(student_id):
        """Edit student"""
        if session.get('user_role') != 'admin':
            flash('Access denied. Admin role required.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        student = Student.query.get_or_404(student_id)
        
        if request.method == 'POST':
            try:
                # Get form data
                roll_number = request.form.get('roll_number')
                name = request.form.get('name')
                phone = request.form.get('phone')
                email = request.form.get('email')
                department = request.form.get('department')
                semester = int(request.form.get('semester', 1))
                
                # Check if roll number is being changed and if it already exists
                if roll_number != student.roll_number:
                    existing_student = Student.query.filter_by(roll_number=roll_number).first()
                    if existing_student:
                        flash(f'❌ Roll number {roll_number} already exists!', 'error')
                        return render_template('edit_student.html', student=student)
                
                # Update student data
                student.roll_number = roll_number
                student.name = name
                student.phone = phone
                student.email = email
                student.department = department
                student.semester = semester
                
                # Commit the transaction
                db.session.commit()
                
                # Refresh the object to ensure we have the latest data
                db.session.refresh(student)
                
                # Clear any cached queries
                db.session.expire_all()
                
                flash('✅ Student updated successfully!', 'success')
                return redirect(url_for('manage_students'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'❌ Error updating student: {str(e)}', 'error')
        
        return render_template('edit_student.html', student=student)
    
    @app.route('/admin/edit-faculty/<int:faculty_id>', methods=['GET', 'POST'])
    @login_required
    def edit_faculty(faculty_id):
        """Edit faculty"""
        if session.get('user_role') != 'admin':
            flash('Access denied. Admin role required.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        faculty = Faculty.query.get_or_404(faculty_id)
        
        if request.method == 'POST':
            try:
                # Get form data
                name = request.form.get('name')
                email = request.form.get('email')
                department = request.form.get('department')
                consultation_time = request.form.get('consultation_time')
                phone = request.form.get('phone')
                
                # Update faculty data
                faculty.name = name
                faculty.email = email
                faculty.department = department
                faculty.consultation_time = consultation_time
                faculty.phone = phone
                
                # Commit the transaction
                db.session.commit()
                
                # Refresh the object to ensure we have the latest data
                db.session.refresh(faculty)
                
                # Clear any cached queries
                db.session.expire_all()
                
                flash('✅ Faculty updated successfully!', 'success')
                return redirect(url_for('manage_faculty'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'❌ Error updating faculty: {str(e)}', 'error')
        
        return render_template('edit_faculty.html', faculty=faculty)
    
    @app.route('/admin/delete-student/<int:student_id>')
    @login_required
    def delete_student(student_id):
        """Delete student"""
        if session.get('user_role') != 'admin':
            flash('Access denied. Admin role required.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        student = Student.query.get_or_404(student_id)
        try:
            db.session.delete(student)
            db.session.commit()
            flash('✅ Student deleted successfully!', 'success')
        except Exception as e:
            flash(f'❌ Error deleting student: {str(e)}', 'error')
        
        return redirect(url_for('manage_students'))
    
    @app.route('/admin/delete-faculty/<int:faculty_id>')
    @login_required
    def delete_faculty(faculty_id):
        """Delete faculty"""
        if session.get('user_role') != 'admin':
            flash('Access denied. Admin role required.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        faculty = Faculty.query.get_or_404(faculty_id)
        try:
            db.session.delete(faculty)
            db.session.commit()
            flash('✅ Faculty deleted successfully!', 'success')
        except Exception as e:
            flash(f'❌ Error deleting faculty: {str(e)}', 'error')
        
        return redirect(url_for('manage_faculty'))
    
    @app.route('/admin/edit-notification/<int:notification_id>', methods=['GET', 'POST'])
    @login_required
    def edit_notification(notification_id):
        """Edit notification"""
        if session.get('user_role') != 'admin':
            flash('Access denied. Admin role required.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        notification = Notification.query.get_or_404(notification_id)
        
        if request.method == 'POST':
            try:
                from datetime import datetime, timedelta
                notification.title = request.form.get('title')
                notification.content = request.form.get('content')
                notification.link_url = request.form.get('link_url')
                notification.file_url = request.form.get('file_url')
                notification.expires_at = datetime.utcnow() + timedelta(days=7)
                db.session.commit()
                flash('✅ Notification updated successfully!', 'success')
                return redirect(url_for('notifications_dashboard'))
            except Exception as e:
                flash(f'❌ Error updating notification: {str(e)}', 'error')
        
        return render_template('edit_notification.html', notification=notification)
    
    @app.route('/admin/delete-notification/<int:notification_id>')
    @login_required
    def delete_notification(notification_id):
        """Delete notification"""
        if session.get('user_role') != 'admin':
            flash('Access denied. Admin role required.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        notification = Notification.query.get_or_404(notification_id)
        try:
            db.session.delete(notification)
            db.session.commit()
            flash('✅ Notification deleted successfully!', 'success')
        except Exception as e:
            flash(f'❌ Error deleting notification: {str(e)}', 'error')
        
        return redirect(url_for('notifications_dashboard'))
    
    @app.route('/admin/generate-weekly-report')
    @login_required
    def generate_weekly_report():
        """Generate weekly report"""
        if session.get('user_role') != 'admin':
            flash('Only admins can generate reports.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        try:
            # Simple weekly report generation
            import csv
            import os
            from datetime import datetime
            
            # Create data directory if it doesn't exist
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
            os.makedirs(data_dir, exist_ok=True)
            
            # Generate CSV filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            csv_filename = f'weekly_report_{timestamp}.csv'
            csv_path = os.path.join(data_dir, csv_filename)
            
            # Create simple weekly report
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Report Type', 'Count', 'Generated At'])
                writer.writerow(['Total Students', Student.query.count(), datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                writer.writerow(['Total Notifications', Notification.query.count(), datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                writer.writerow(['Total Results', Result.query.count(), datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                writer.writerow(['Total Fee Records', FeeRecord.query.count(), datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                writer.writerow(['Pending Payments', FeeRecord.query.filter(FeeRecord.balance_amount > 0).count(), datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            
            flash(f'✅ Weekly report generated successfully! File: {csv_filename}', 'success')
            
        except Exception as e:
            flash(f'❌ Error generating report: {str(e)}', 'error')
        
        return redirect(url_for('admin_dashboard'))
    
    @app.route('/admin/dashboard')
    @login_required
    def admin_dashboard():
        """Admin dashboard"""
        # Get statistics
        total_students = Student.query.count()
        total_notifications = Notification.query.count()
        active_notifications = Notification.query.filter(Notification.expires_at > datetime.utcnow()).count()
        total_complaints = Complaint.query.count()
        pending_complaints = Complaint.query.filter_by(status='pending').count()
        
        # Recent notifications
        recent_notifications = Notification.query.filter(
            Notification.expires_at > datetime.utcnow()
        ).order_by(Notification.created_at.desc()).limit(5).all()
        
        return render_template('admin_dashboard_simple.html',
                             total_students=total_students,
                             total_notifications=total_notifications,
                             active_notifications=active_notifications,
                             total_complaints=total_complaints,
                             pending_complaints=pending_complaints,
                             recent_notifications=recent_notifications)
    
    @app.route('/admin/analytics')
    @login_required
    def analytics():
        """Analytics dashboard"""
        if session.get('user_role') != 'admin':
            flash('Access denied. Admin role required.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        # Simple analytics data
        analytics_data = {
            'total_queries': 10,
            'unknown_queries': 3,
            'top_unknown': ['help', 'hi', 'hello'],
            'registered_students': Student.query.count(),
            'result_queries_today': 0,
            'fee_queries_today': 0,
            'result_queries_week': 0,
            'fee_queries_week': 0,
        }
        
        return render_template('analytics.html', analytics=analytics_data)
    
    # WhatsApp Webhook Routes
    @app.route('/webhook/whatsapp', methods=['POST'])
    def whatsapp_webhook():
        """Twilio WhatsApp webhook"""
        try:
            incoming_msg = request.values.get('Body', '').strip()
            from_number = request.values.get('From', '').replace('whatsapp:', '')
            
            # Initialize chatbot service
            chatbot = ChatbotService()
            
            # Process message
            response = chatbot.process_message(incoming_msg, from_number)
            
            # Escape XML special characters
            response_escaped = response.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            return f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{response_escaped}</Message></Response>', 200, {'Content-Type': 'text/xml'}
        except Exception as e:
            app.logger.error(f"WhatsApp webhook error: {str(e)}")
            return f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>Sorry, an error occurred. Please try again later.</Message></Response>', 200, {'Content-Type': 'text/xml'}
    
    @app.route('/webhook/whatsapp/status', methods=['POST'])
    def whatsapp_status():
        """Twilio status callback (optional)"""
        return '', 200
    
    # API Routes for Admin Dashboard
    @app.route('/api/notifications', methods=['GET'])
    @login_required
    def get_notifications():
        """Get all notifications"""
        notifications = Notification.query.order_by(Notification.created_at.desc()).all()
        return jsonify([{
            'id': n.id,
            'title': n.title,
            'content': n.content,
            'file_url': n.file_url,
            'link_url': n.link_url,
            'created_at': n.created_at.isoformat(),
            'expires_at': n.expires_at.isoformat(),
            'is_expired': n.is_expired()
        } for n in notifications])
    
    @app.route('/api/students/search', methods=['GET'])
    @login_required
    def search_students():
        """Search students"""
        query = request.args.get('q', '')
        if len(query) < 2:
            return jsonify([])
        
        students = Student.query.filter(
            (Student.roll_number.contains(query)) |
            (Student.name.contains(query)) |
            (Student.phone.contains(query))
        ).limit(20).all()
        
        return jsonify([{
            'id': s.id,
            'roll_number': s.roll_number,
            'name': s.name,
            'phone': s.phone,
            'email': s.email,
            'department': s.department,
            'semester': s.semester
        } for s in students])
    
    @app.route('/api/faculty/search', methods=['GET'])
    def search_faculty():
        """Search faculty (public endpoint for chatbot)"""
        query = request.args.get('q', '')
        if len(query) < 2:
            return jsonify([])
        
        faculty = Faculty.query.filter(
            (Faculty.name.contains(query)) |
            (Faculty.department.contains(query))
        ).limit(20).all()
        
        return jsonify([{
            'id': f.id,
            'name': f.name,
            'email': f.email,
            'department': f.department,
            'consultation_time': f.consultation_time,
            'phone': f.phone
        } for f in faculty])
    
    # Telegram Bot Routes
    @app.route('/webhook/telegram', methods=['POST'])
    def telegram_webhook():
        """Telegram webhook endpoint"""
        try:
            from app.services.telegram_service import TelegramBotService
            
            # Log incoming request
            current_app.logger.info("Telegram webhook received request")
            
            # Token comes from config / environment (preferred), or from the setup UI session.
            bot_token = (current_app.config.get('TELEGRAM_BOT_TOKEN') or session.get('telegram_bot_token') or '').strip()
            if not bot_token:
                current_app.logger.error("TELEGRAM_BOT_TOKEN is not configured for Telegram webhook")
                return jsonify({'error': 'TELEGRAM_BOT_TOKEN is not configured'}), 500
            
            # Initialize bot service
            bot_service = TelegramBotService()
            bot_service.bot_token = bot_token
            
            # Process update
            update = request.get_json()
            current_app.logger.info(f"Received update: {update}")
            
            if update:
                result = bot_service.process_update(update)
                current_app.logger.info(f"Bot service result: {result}")
            
            return '', 200
            
        except Exception as e:
            current_app.logger.error(f"Telegram webhook error: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/telegram/setup', methods=['GET', 'POST'])
    def telegram_setup():
        """Telegram bot setup page"""
        if request.method == 'POST':
            bot_token = request.form.get('bot_token')
            default_webhook = request.url_root.rstrip('/') + url_for('telegram.telegram_webhook')
            webhook_url = request.form.get('webhook_url') or default_webhook
            
            if not bot_token:
                flash('Bot token is required', 'error')
                return render_template('telegram_setup.html')
            
            try:
                from app.services.telegram_service import TelegramBotService
                
                bot_service = TelegramBotService()
                if bot_service.initialize(bot_token, webhook_url):
                    # Save token to session for webhook
                    from flask import session
                    session['telegram_bot_token'] = bot_token
                    
                    # Get bot info
                    bot_info = bot_service.get_bot_info()
                    if bot_info:
                        flash(f'Telegram bot "{bot_info.get("username")}" connected successfully!', 'success')
                        return render_template('telegram_setup.html', bot_info=bot_info)
                
                flash('Failed to connect Telegram bot. Please check your token.', 'error')
                
            except Exception as e:
                flash(f'Error setting up Telegram bot: {str(e)}', 'error')
        
        return render_template('telegram_setup.html')

    # Admin Upload Routes
    @app.route('/admin/upload')
    @login_required
    @admin_required
    def admin_upload():
        """Admin upload page"""
        return render_template('admin_upload.html')


    @app.route('/admin/upload/students', methods=['POST'])
    @login_required
    @admin_required
    def upload_students():
        """Upload students data"""
        from app.services.upload_service import DatabaseUploadService
        from werkzeug.utils import secure_filename
        import os
        
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('admin_upload'))
        
        file = request.files['file']
        mode = request.form.get('mode', 'append')
        
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('admin_upload'))
        
        if not DatabaseUploadService.allowed_file(file.filename):
            flash('Invalid file type. Please upload Excel or CSV file.', 'error')
            return redirect(url_for('admin_upload'))
        
        try:
            # Save file temporarily
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Process upload
            result = DatabaseUploadService.upload_students(file_path, mode)
            
            # Clean up
            os.remove(file_path)
            
            if result['success']:
                flash(result['message'], 'success')
                if result['errors']:
                    flash(f'Warnings: {len(result["errors"])} rows had errors.', 'warning')
                else:
                    flash(result['message'], 'error')
                for error in result['errors'][:5]:  # Show first 5 errors
                    flash(error, 'error')
            
            return redirect(url_for('admin_upload'))
            
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'error')
            return redirect(url_for('admin_upload'))


    @app.route('/admin/upload/faculty', methods=['POST'])
    @login_required
    @admin_required
    def upload_faculty():
        """Upload faculty data"""
        from app.services.upload_service import DatabaseUploadService
        from werkzeug.utils import secure_filename
        import os
        
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('admin_upload'))
        
        file = request.files['file']
        mode = request.form.get('mode', 'append')
        
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('admin_upload'))
        
        if not DatabaseUploadService.allowed_file(file.filename):
            flash('Invalid file type. Please upload Excel or CSV file.', 'error')
            return redirect(url_for('admin_upload'))
        
        try:
            # Save file temporarily
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Process upload
            result = DatabaseUploadService.upload_faculty(file_path, mode)
            
            # Clean up
            os.remove(file_path)
            
            if result['success']:
                flash(result['message'], 'success')
                if result['errors']:
                    flash(f'Warnings: {len(result["errors"])} rows had errors.', 'warning')
                else:
                    flash(result['message'], 'error')
                for error in result['errors'][:5]:  # Show first 5 errors
                    flash(error, 'error')
            
            return redirect(url_for('admin_upload'))
            
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'error')
            return redirect(url_for('admin_upload'))


    @app.route('/admin/upload/fees', methods=['POST'])
    @login_required
    @admin_required
    def upload_fees():
        """Upload fees data"""
        from app.services.upload_service import DatabaseUploadService
        from werkzeug.utils import secure_filename
        import os
        
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('admin_upload'))
        
        file = request.files['file']
        mode = request.form.get('mode', 'append')
        
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('admin_upload'))
        
        if not DatabaseUploadService.allowed_file(file.filename):
            flash('Invalid file type. Please upload Excel or CSV file.', 'error')
            return redirect(url_for('admin_upload'))
        
        try:
            # Save file temporarily
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Process upload
            result = DatabaseUploadService.upload_fees(file_path, mode)
            
            # Clean up
            os.remove(file_path)
            
            if result['success']:
                flash(result['message'], 'success')
                if result['errors']:
                    flash(f'Warnings: {len(result["errors"])} rows had errors.', 'warning')
                else:
                    flash(result['message'], 'error')
                for error in result['errors'][:5]:  # Show first 5 errors
                    flash(error, 'error')
            
            return redirect(url_for('admin_upload'))
            
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'error')
            return redirect(url_for('admin_upload'))


    @app.route('/admin/upload/results', methods=['POST'])
    @login_required
    @admin_required
    def upload_results():
        """Upload results data"""
        from app.services.upload_service import DatabaseUploadService
        from werkzeug.utils import secure_filename
        import os
        
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('admin_upload'))
        
        file = request.files['file']
        mode = request.form.get('mode', 'append')
        
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('admin_upload'))
        
        if not DatabaseUploadService.allowed_file(file.filename):
            flash('Invalid file type. Please upload Excel or CSV file.', 'error')
            return redirect(url_for('admin_upload'))
        
        try:
            # Save file temporarily
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Process upload
            result = DatabaseUploadService.upload_results(file_path, mode)
            
            # Clean up
            os.remove(file_path)
            
            if result['success']:
                flash(result['message'], 'success')
                if result['errors']:
                    flash(f'Warnings: {len(result["errors"])} rows had errors.', 'warning')
                else:
                    flash(result['message'], 'error')
                for error in result['errors'][:5]:  # Show first 5 errors
                    flash(error, 'error')
            
            return redirect(url_for('admin_upload'))
            
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'error')
            return redirect(url_for('admin_upload'))

    @app.route('/admin/manage-complaints')
    @login_required
    def manage_complaints():
        """Manage all complaints (admin only)"""
        if session.get('user_role') != 'admin':
            flash('Access denied. Admin role required.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        # Get complaints with student info
        complaints = db.session.query(Complaint, Student).join(Student).order_by(Complaint.created_at.desc()).all()
        return render_template('manage_complaints.html', complaints=complaints)
    
    @app.route('/admin/update-complaint/<int:complaint_id>', methods=['POST'])
    @login_required
    def update_complaint(complaint_id):
        """Update complaint status"""
        if session.get('user_role') != 'admin':
            flash('Access denied. Admin role required.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        complaint = Complaint.query.get_or_404(complaint_id)
        new_status = request.form.get('status')
        old_status = complaint.status
        
        if new_status in ['pending', 'investigating', 'resolved']:
            complaint.status = new_status
            db.session.commit()
            
            # Send notification about status update
            try:
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
            
            flash('✅ Complaint status updated successfully!', 'success')
        else:
            flash('❌ Invalid status.', 'error')
        
        return redirect(url_for('manage_complaints'))
    
    @app.route('/admin/delete-complaint/<int:complaint_id>')
    @login_required
    def delete_complaint(complaint_id):
        """Delete complaint"""
        if session.get('user_role') != 'admin':
            flash('Access denied. Admin role required.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        complaint = Complaint.query.get_or_404(complaint_id)
        try:
            db.session.delete(complaint)
            db.session.commit()
            flash('✅ Complaint deleted successfully!', 'success')
        except Exception as e:
            flash(f'❌ Error deleting complaint: {str(e)}', 'error')
        
        return redirect(url_for('manage_complaints'))

    @app.route('/admin/complaint-messages')
    @login_required
    def complaint_messages():
        """View only complaint messages (separate from notifications)"""
        if session.get('user_role') != 'admin':
            flash('Access denied. Admin role required.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        # Get only complaint-related notifications
        complaint_notifications = Notification.query.filter_by(notification_type='complaint').order_by(Notification.created_at.desc()).all()
        complaint_updates = Notification.query.filter_by(notification_type='complaint_update').order_by(Notification.created_at.desc()).all()
        
        return render_template('complaint_messages.html', 
                             complaint_notifications=complaint_notifications,
                             complaint_updates=complaint_updates)

    @app.route('/admin/manage-faqs')
    @login_required
    def manage_faqs():
        """Manage FAQs"""
        if session.get('user_role') != 'admin':
            flash('Access denied. Admin role required.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        # Get filter parameters
        search = request.args.get('search', '')
        selected_category = request.args.get('category', '')
        selected_priority = request.args.get('priority', '')
        page = request.args.get('page', 1, type=int)
        
        # Build query
        query = FAQ.query
        
        if search:
            query = query.filter(FAQ.question.ilike(f'%{search}%'))
        
        if selected_category:
            query = query.filter(FAQ.category == selected_category)
        
        if selected_priority:
            query = query.filter(FAQ.priority == int(selected_priority))
        
        # Pagination
        per_page = 10
        faqs = query.order_by(FAQ.priority.desc(), FAQ.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Get categories for filter
        categories = db.session.query(FAQ.category).distinct().all()
        categories = [(cat[0], cat[0]) for cat in categories]
        
        return render_template('manage_faqs.html', 
                             faqs=faqs,
                             search=search,
                             selected_category=selected_category,
                             selected_priority=selected_priority,
                             categories=categories)

    @app.route('/admin/add-faq', methods=['GET', 'POST'])
    @login_required
    def add_faq():
        """Add new FAQ"""
        if session.get('user_role') != 'admin':
            flash('Access denied. Admin role required.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        if request.method == 'POST':
            try:
                faq = FAQ(
                    question=request.form.get('question'),
                    answer=request.form.get('answer'),
                    category=request.form.get('category', 'general'),
                    priority=int(request.form.get('priority', 2)),
                    is_active='is_active' in request.form
                )
                db.session.add(faq)
                db.session.commit()
                flash('✅ FAQ added successfully!', 'success')
                return redirect(url_for('manage_faqs'))
                
            except Exception as e:
                flash(f'❌ Error adding FAQ: {str(e)}', 'error')
        
        return render_template('add_faq.html')

    @app.route('/admin/edit-faq/<int:faq_id>', methods=['GET', 'POST'])
    @login_required
    def edit_faq(faq_id):
        """Edit existing FAQ"""
        if session.get('user_role') != 'admin':
            flash('Access denied. Admin role required.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        faq = FAQ.query.get_or_404(faq_id)
        
        if request.method == 'POST':
            try:
                faq.question = request.form.get('question')
                faq.answer = request.form.get('answer')
                faq.category = request.form.get('category', 'general')
                faq.priority = int(request.form.get('priority', 2))
                faq.is_active = 'is_active' in request.form
                db.session.commit()
                flash('✅ FAQ updated successfully!', 'success')
                return redirect(url_for('manage_faqs'))
                
            except Exception as e:
                flash(f'❌ Error updating FAQ: {str(e)}', 'error')
        
        return render_template('edit_faq.html', faq=faq)

    @app.route('/admin/delete-faq/<int:faq_id>', methods=['POST'])
    @login_required
    def delete_faq(faq_id):
        """Delete FAQ"""
        if session.get('user_role') != 'admin':
            flash('Access denied. Admin role required.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        faq = FAQ.query.get_or_404(faq_id)
        
        try:
            db.session.delete(faq)
            db.session.commit()
            flash('✅ FAQ deleted successfully!', 'success')
        except Exception as e:
            flash(f'❌ Error deleting FAQ: {str(e)}', 'error')
        
        return redirect(url_for('manage_faqs'))

    @app.route('/admin/faq-records')
    @login_required
    def faq_records():
        """View FAQ records and processing history"""
        if session.get('user_role') != 'admin':
            flash('Access denied. Admin role required.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        # Get all FAQ records for display
        faqs = FAQ.query.order_by(FAQ.created_at.desc()).all()
        
        return render_template('faq_records.html', faqs=faqs)

    @app.route('/admin/create-faq-from-complaint/<int:notification_id>')
    @login_required
    def create_faq_from_complaint(notification_id):
        """Create FAQ from complaint notification"""
        if session.get('user_role') != 'admin':
            flash('Access denied. Admin role required.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        notification = Notification.query.get_or_404(notification_id)
        
        if request.method == 'POST':
            try:
                from app.models import FAQ
                # Extract complaint details from notification content
                content_lines = notification.content.split('\n')
                question = ""
                category = "complaint"
                priority = 3  # High priority for complaints
                
                # Parse complaint details
                for line in content_lines:
                    if 'Student:' in line:
                        student_info = line.split('Student:')[1].strip()
                        question = f"What is the process for filing complaints regarding {student_info}?"
                    elif 'Category:' in line:
                        category = line.split('Category:')[1].strip().lower()
                    elif 'Description:' in line:
                        desc = line.split('Description:')[1].strip()
                        question = f"How to report {category} issues like: {desc[:50]}...?"
                
                if not question:
                    question = "How to file a complaint?"
                
                # Create FAQ
                faq = FAQ(
                    question=question,
                    answer=get_complaint_faq_answer(),
                    category=category,
                    priority=priority,
                    is_active=True
                )
                db.session.add(faq)
                db.session.commit()
                
                flash('✅ FAQ created successfully from complaint message!', 'success')
                return redirect(url_for('admin.manage_faqs'))
                
            except Exception as e:
                flash(f'❌ Error creating FAQ: {str(e)}', 'error')
        
        return render_template('create_faq_from_complaint.html', notification=notification)

def get_complaint_faq_answer():
    """Get standard answer for complaint FAQ"""
    return """**How to File a Complaint:**

📝 **Step-by-Step Process:**

1️⃣ **Choose Your Category:**
   • `ragging` - Anti-ragging complaints
   • `harassment` - Harassment issues  
   • `other` - Other complaints

2️⃣ **Format Your Message:**
   Use: `complaint <category> <description>`

3️⃣ **Provide Details:**
   • Be specific about incident
   • Include date, time, location if applicable
   • Mention names if necessary
   • Minimum 10 characters description

4️⃣ **Submit:**
   • Send via chatbot/WhatsApp
   • Immediate admin notification
   • Get complaint ID for tracking

📞 **For Urgent Issues:**
   • Contact admin office: +91-12345-67890
   • Email: admin@college.edu
   • Visit admin office in person

⚡ **Response Time:**
   • Admin reviews within 24 hours
   • Status updates provided
   • Action taken promptly

---
*This FAQ is automatically generated from complaint patterns*"""

    @app.route('/admin/delete-complaint-notification/<int:notification_id>')
    @login_required
    def delete_complaint_notification(notification_id):
        """Delete complaint notification"""
        if session.get('user_role') != 'admin':
            flash('Access denied. Admin role required.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        notification = Notification.query.get_or_404(notification_id)
        try:
            db.session.delete(notification)
            db.session.commit()
            flash('✅ Complaint notification deleted successfully!', 'success')
        except Exception as e:
            flash(f'❌ Error deleting notification: {str(e)}', 'error')
        
        return redirect(url_for('complaint_messages'))

    # Close the register_routes function
