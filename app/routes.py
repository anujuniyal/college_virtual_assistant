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

from app.extensions import db
from app.models import (
    Admin, Student, Faculty, Notification, 
    Result, FeeRecord, Complaint, ChatbotQA, ChatbotUnknown
)
from app.chatbot.service import ChatbotService

from app.services.otp_service import OTPService


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
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Multi-role login system"""
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
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
            else:
                flash('Invalid username or password', 'error')
        
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
            
            # Hardcoded token for now (temporary solution)
            bot_token = "7671092916:AAG4GMyeTli6V9rEF6GH9H_HliV4QRq8Guw"
            
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
            webhook_url = request.form.get('webhook_url', f"https://7c5760bf05a5.ngrok-free.app/webhook/telegram")
            
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

    # Close the register_routes function
