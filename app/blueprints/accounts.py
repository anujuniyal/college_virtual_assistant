from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Student, Faculty, Notification, Complaint, Result, FeeRecord
from app.services.safe_execute import safe_execute
from datetime import datetime
from functools import wraps

accounts_bp = Blueprint('accounts', __name__, url_prefix='/accounts')

def get_user_role():
    """Get current user's role"""
    if not current_user.is_authenticated:
        return 'student'
    
    # Handle both Admin and Faculty models
    if hasattr(current_user, 'role'):
        return current_user.role
    elif hasattr(current_user, 'user_role'):
        return current_user.user_role
    else:
        return 'student'

def has_write_access():
    """Check if current user has write access to accounts"""
    user_role = get_user_role()
    return user_role == 'accounts'

def accounts_required(write_access=False):
    """Decorator to ensure user has accounts privileges with optional write access"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            user_role = get_user_role()
            
            # Check accounts access - allow admin, faculty, and accounts roles for read-only
            if user_role not in ['admin', 'faculty', 'accounts']:
                flash('Access denied. Accounts privileges required.', 'error')
                return redirect(url_for('auth.login'))
            
            # Check write access for fee operations - only accounts role can write
            if write_access and user_role not in ['accounts']:
                flash('Write access required for fee operations. Contact admin for accounts role.', 'error')
                return redirect(url_for('auth.login'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def accounts_dashboard_required():
    """Decorator to restrict access to accounts dashboard - only accounts role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            user_role = get_user_role()
            
            # Only allow accounts role for dashboard access
            if user_role not in ['accounts']:
                flash('Access denied. Accounts dashboard privileges required.', 'error')
                return redirect(url_for('auth.login'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@accounts_bp.route('/dashboard')
@login_required
@accounts_dashboard_required()
def accounts_dashboard():
    """Accounts dashboard with financial access"""
    try:
        # Get real statistics
        total_students = safe_execute(lambda: Student.query.count()) or 0
        total_fee_records = safe_execute(lambda: FeeRecord.query.count()) or 0
        total_notifications = safe_execute(lambda: Notification.query.count()) or 0
        
        # Only show fee records to accounts users, not to admin/faculty
        user_role = get_user_role()
        if user_role != 'accounts':
            total_fee_records = 0
            total_notifications = safe_execute(lambda: Notification.query.count()) or 0
        
        # Calculate pending fees
        pending_count = 0
        pending_amount = 0
        collection_rate = 0
        
        try:
            fee_records = safe_execute(lambda: FeeRecord.query.all()) or []
            for record in fee_records:
                if record.balance > 0:
                    pending_count += 1
                    pending_amount += record.balance
            
            total_amount = sum(record.total_amount for record in fee_records) if fee_records else 0
            paid_amount = sum(record.paid_amount for record in fee_records) if fee_records else 0
            
            if total_amount > 0:
                collection_rate = round((paid_amount / total_amount) * 100, 1)
        except Exception as e:
            current_app.logger.error(f"Error calculating fee statistics: {str(e)}")
        
        return render_template('accounts_dashboard.html',
                             total_students=total_students,
                             total_fee_records=total_fee_records,
                             total_notifications=total_notifications,
                             total_pending=pending_count,
                             pending_amount=pending_amount,
                             collection_rate=collection_rate)
    except Exception as e:
        current_app.logger.error(f"Error loading accounts dashboard: {str(e)}")
        flash('Error loading accounts dashboard.', 'error')
        return render_template('accounts_dashboard.html',
                             total_students=0,
                             total_fee_records=0,
                             total_notifications=0,
                             total_pending=0,
                             pending_amount=0,
                             collection_rate=0)

@accounts_bp.route('/students-fees-simple')
@login_required
@accounts_required()
def students_fees_simple():
    """Simplified students fee records view with direct return to role dashboard"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        search = request.args.get('search', '').strip()
        fee_status = request.args.get('fee_status', '').strip()
        semester = request.args.get('semester', '').strip()
        
        # Build query
        query = Student.query
        
        # Apply search filter
        if search:
            query = query.filter(
                db.or_(
                    Student.name.ilike(f'%{search}%'),
                    Student.roll_number.ilike(f'%{search}%'),
                    Student.email.ilike(f'%{search}%'),
                    Student.department.ilike(f'%{search}%')
                )
            )
        
        # Apply filters
        if semester:
            query = query.filter(Student.semester == int(semester))
        
        # Get students with pagination
        students_pagination = safe_execute(
            lambda: query.order_by(Student.name)
            .paginate(page=page, per_page=per_page, error_out=False)
        )
        
        students = students_pagination.items if students_pagination else []
        
        # Calculate fee status for each student
        students_with_fees = []
        fully_paid_count = 0
        partial_payment_count = 0
        unpaid_count = 0
        
        for student in students:
            # Get latest fee record
            latest_fee = safe_execute(
                lambda: FeeRecord.query.filter_by(student_id=student.id)
                .order_by(FeeRecord.last_updated.desc())
                .first()
            )
            
            # Determine fee status
            status = 'no_record'
            if latest_fee:
                if latest_fee.balance <= 0:
                    status = 'paid'
                    fully_paid_count += 1
                elif latest_fee.paid_amount > 0:
                    status = 'partial'
                    partial_payment_count += 1
                else:
                    status = 'unpaid'
                    unpaid_count += 1
            
            # Apply fee status filter
            if fee_status and status != fee_status:
                continue
            
            student.latest_fee = latest_fee
            student.fee_status = status
            students_with_fees.append(student)
        
        # Determine role-based return URL and title
        user_role = get_user_role()
        if user_role == 'admin':
            return_url = url_for('admin.admin_dashboard')
            role_title = 'Admin'
        elif user_role == 'faculty':
            return_url = url_for('faculty.faculty_dashboard')
            role_title = 'Faculty'
        else:
            return_url = url_for('accounts.accounts_dashboard')
            role_title = 'Accounts'
        
        # Allow edit only for accounts role
        allow_edit = (user_role == 'accounts')
        
        return render_template('students_fees_simple.html',
                             students=students_with_fees,
                             pagination=students_pagination,
                             page=page,
                             total_students=len(students_with_fees),
                             fully_paid_count=fully_paid_count,
                             partial_payment_count=partial_payment_count,
                             unpaid_count=unpaid_count,
                             return_url=return_url,
                             role_title=role_title,
                             allow_edit=allow_edit)
    
    except Exception as e:
        current_app.logger.error(f"Error loading students fees simple view: {str(e)}")
        flash('Error loading students fees view.', 'error')
        
        # Determine role-based return URL even on error
        user_role = get_user_role()
        if user_role == 'admin':
            return_url = url_for('admin.admin_dashboard')
            role_title = 'Admin'
        elif user_role == 'faculty':
            return_url = url_for('faculty.faculty_dashboard')
            role_title = 'Faculty'
        else:
            return_url = url_for('accounts.accounts_dashboard')
            role_title = 'Accounts'
        
        return render_template('students_fees_simple.html',
                             students=[],
                             pagination=None,
                             page=1,
                             total_students=0,
                             fully_paid_count=0,
                             partial_payment_count=0,
                             unpaid_count=0,
                             return_url=return_url,
                             role_title=role_title,
                             allow_edit=False)

@accounts_bp.route('/students-fees')
@login_required
@accounts_required()
def students_fees_dashboard():
    """Students with fee status and CRUD operations"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        search = request.args.get('search', '').strip()
        fee_status = request.args.get('fee_status', '').strip()
        semester = request.args.get('semester', '').strip()
        
        # Build query
        query = Student.query
        
        # Apply search filter
        if search:
            query = query.filter(
                db.or_(
                    Student.name.ilike(f'%{search}%'),
                    Student.roll_number.ilike(f'%{search}%'),
                    Student.email.ilike(f'%{search}%'),
                    Student.department.ilike(f'%{search}%')
                )
            )
        
        # Apply filters
        if semester:
            query = query.filter(Student.semester == int(semester))
        
        # Get students with pagination
        students_pagination = safe_execute(
            lambda: query.order_by(Student.name)
            .paginate(page=page, per_page=per_page, error_out=False)
        )
        
        students = students_pagination.items if students_pagination else []
        
        # Calculate fee status for each student
        students_with_fees = []
        fully_paid_count = 0
        partial_payment_count = 0
        unpaid_count = 0
        
        for student in students:
            # Get latest fee record
            latest_fee = safe_execute(
                lambda: FeeRecord.query.filter_by(student_id=student.id)
                .order_by(FeeRecord.last_updated.desc())
                .first()
            )
            
            # Determine fee status
            status = 'no_record'
            if latest_fee:
                if latest_fee.balance <= 0:
                    status = 'paid'
                    fully_paid_count += 1
                elif latest_fee.paid_amount > 0:
                    status = 'partial'
                    partial_payment_count += 1
                else:
                    status = 'unpaid'
                    unpaid_count += 1
            
            # Apply fee status filter
            if fee_status and status != fee_status:
                continue
            
            student.latest_fee = latest_fee
            student.fee_status = status
            students_with_fees.append(student)
        
        # Use read-only template for admin/faculty users, full template for accounts users
        if get_user_role() == 'accounts':
            return render_template('students_fees_dashboard.html',
                                 students=students_with_fees,
                                 pagination=students_pagination,
                                 page=page,
                                 total_students=len(students_with_fees),
                                 fully_paid_count=fully_paid_count,
                                 partial_payment_count=partial_payment_count,
                                 unpaid_count=unpaid_count)
        else:
            return render_template('students_fees_readonly.html',
                                 students=students_with_fees,
                                 pagination=students_pagination,
                                 page=page,
                                 user=current_user)
    
    except Exception as e:
        current_app.logger.error(f"Error loading students fees dashboard: {str(e)}")
        flash('Error loading students fees dashboard.', 'error')
        return render_template('students_fees_dashboard.html',
                             students=[],
                             pagination=None,
                             page=1,
                             total_students=0,
                             fully_paid_count=0,
                             partial_payment_count=0,
                             unpaid_count=0)

@accounts_bp.route('/student/<int:student_id>/details', methods=['GET'])
@login_required
@accounts_required()
def get_student_details(student_id):
    """Get student details for modal"""
    try:
        student = safe_execute(
            lambda: Student.query.get_or_404(student_id)
        )
        
        if student:
            # Get latest fee record
            latest_fee = safe_execute(
                lambda: FeeRecord.query.filter_by(student_id=student.id)
                .order_by(FeeRecord.last_updated.desc())
                .first()
            )
            
            return jsonify({
                'success': True,
                'student': {
                    'id': student.id,
                    'roll_number': student.roll_number,
                    'name': student.name,
                    'email': student.email,
                    'phone': student.phone,
                    'department': student.department,
                    'semester': student.semester,
                    'telegram_user_id': student.telegram_user_id,
                    'telegram_verified': student.telegram_verified,
                    'telegram_info': student.get_telegram_info(),
                    'latest_fee': {
                        'total_amount': latest_fee.total_amount if latest_fee else 0,
                        'paid_amount': latest_fee.paid_amount if latest_fee else 0,
                        'balance': latest_fee.balance if latest_fee else 0,
                        'last_updated': latest_fee.last_updated.isoformat() if latest_fee else None
                    } if latest_fee else None
                }
            })
        else:
            return jsonify({'success': False, 'message': 'Student not found'}), 404
    
    except Exception as e:
        current_app.logger.error(f"Error getting student details: {str(e)}")
        return jsonify({'success': False, 'message': 'Error loading student details'}), 500

@accounts_bp.route('/student/<int:student_id>/add-payment', methods=['POST'])
@login_required
@accounts_required(write_access=True)
def add_student_payment(student_id):
    """Add payment for student"""
    try:
        data = request.get_json()
        
        if not data or 'amount' not in data:
            return jsonify({'success': False, 'message': 'Payment amount is required'}), 400
        
        student = safe_execute(
            lambda: Student.query.get_or_404(student_id)
        )
        
        if not student:
            return jsonify({'success': False, 'message': 'Student not found'}), 404
        
        # Get or create fee record
        fee_record = safe_execute(
            lambda: FeeRecord.query.filter_by(student_id=student.id)
            .order_by(FeeRecord.last_updated.desc())
            .first()
        )
        
        if not fee_record:
            return jsonify({'success': False, 'message': 'No fee record found for this student'}), 404
        
        # Update payment
        fee_record.paid_amount += float(data['amount'])
        fee_record.update_balance()
        fee_record.last_updated = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Payment added successfully',
            'new_balance': fee_record.balance
        })
    
    except Exception as e:
        current_app.logger.error(f"Error adding payment: {str(e)}")
        return jsonify({'success': False, 'message': 'Error adding payment'}), 500

@accounts_bp.route('/manage-accounts')
@login_required
@accounts_required()
def manage_accounts():
    """Manage college accounts and finances"""
    try:
        students = safe_execute(
            lambda: Student.query.order_by(Student.name).all()
        ) or []
        faculty_members = safe_execute(
            lambda: Faculty.query.order_by(Faculty.name).all()
        ) or []
        
        return render_template('manage_accounts.html', 
                             students=students, 
                             faculty_members=faculty_members)
    except Exception as e:
        flash('Error loading accounts.', 'error')
        return render_template('manage_accounts.html', 
                             students=[], 
                             faculty_members=[])

@accounts_bp.route('/manage-notifications')
@login_required
@accounts_required()
def manage_notifications():
    """Manage notifications for accounts"""
    try:
        # Get notifications for accounts role
        notifications = safe_execute(
            lambda: Notification.query.order_by(Notification.created_at.desc()).limit(10).all()
        ) or []
        
        return render_template('accounts_manage_notifications.html', notifications=notifications)
    except Exception as e:
        current_app.logger.error(f"Error loading notifications: {str(e)}")
        flash('Error loading notifications.', 'error')
        return render_template('accounts_manage_notifications.html', notifications=[])


@accounts_bp.route('/billing')
@login_required
@accounts_required()
def billing():
    """Billing and financial management"""
    try:
        # Get billing data
        total_students = safe_execute(lambda: Student.query.count()) or 0
        total_faculty = safe_execute(lambda: Faculty.query.count()) or 0
        
        # Calculate financial data from fee records
        fee_records = safe_execute(lambda: FeeRecord.query.all()) or []
        total_collected = sum(record.paid_amount for record in fee_records) if fee_records else 0
        total_pending = sum(record.balance for record in fee_records if record.balance > 0) if fee_records else 0
        total_revenue = sum(record.total_amount for record in fee_records) if fee_records else 0
        
        return render_template('billing.html',
                             total_students=total_students,
                             total_faculty=total_faculty,
                             total_collected=total_collected,
                             total_pending=total_pending,
                             total_revenue=total_revenue)
    except Exception as e:
        current_app.logger.error(f"Error loading billing: {str(e)}")
        flash('Error loading billing.', 'error')
        return redirect(url_for('accounts.accounts_dashboard'))

@accounts_bp.route('/student/<int:student_id>/update-fee', methods=['POST'])
@login_required
@accounts_required(write_access=True)
def update_student_fee(student_id):
    """Update student fee record"""
    try:
        data = request.get_json()
        
        if not data or 'semester' not in data or 'total_amount' not in data or 'paid_amount' not in data:
            return jsonify({'success': False, 'message': 'All fee fields are required'}), 400
        
        student = safe_execute(
            lambda: Student.query.get_or_404(student_id)
        )
        
        if not student:
            return jsonify({'success': False, 'message': 'Student not found'}), 404
        
        # Get or create fee record
        fee_record = safe_execute(
            lambda: FeeRecord.query.filter_by(student_id=student.id, semester=int(data['semester']))
            .first()
        )
        
        if fee_record:
            # Update existing record
            fee_record.total_amount = float(data['total_amount'])
            fee_record.paid_amount = float(data['paid_amount'])
            fee_record.update_balance()
            fee_record.last_updated = datetime.utcnow()
        else:
            # Create new record
            fee_record = FeeRecord(
                student_id=student.id,
                semester=int(data['semester']),
                total_amount=float(data['total_amount']),
                paid_amount=float(data['paid_amount']),
                balance_amount=float(data['total_amount']) - float(data['paid_amount'])
            )
            db.session.add(fee_record)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Fee record updated successfully',
            'new_balance': fee_record.balance
        })
    
    except Exception as e:
        current_app.logger.error(f"Error updating fee record: {str(e)}")
        return jsonify({'success': False, 'message': 'Error updating fee record'}), 500

@accounts_bp.route('/student/<int:student_id>/payment-history', methods=['GET'])
@login_required
@accounts_required()
def get_payment_history(student_id):
    """Get payment history for student"""
    try:
        student = safe_execute(
            lambda: Student.query.get_or_404(student_id)
        )
        
        if not student:
            return jsonify({'success': False, 'message': 'Student not found'}), 404
        
        # Get all fee records for the student (this would be payment history in a real system)
        fee_records = safe_execute(
            lambda: FeeRecord.query.filter_by(student_id=student.id)
            .order_by(FeeRecord.last_updated.desc())
            .all()
        ) or []
        
        history = []
        for record in fee_records:
            history.append({
                'date': record.last_updated.isoformat(),
                'semester': record.semester,
                'total_amount': record.total_amount,
                'paid_amount': record.paid_amount,
                'balance': record.balance,
                'method': 'System Record'  # In a real system, this would track actual payment methods
            })
        
        return jsonify({
            'success': True,
            'student': {
                'id': student.id,
                'name': student.name,
                'roll_number': student.roll_number
            },
            'history': history
        })
    
    except Exception as e:
        current_app.logger.error(f"Error getting payment history: {str(e)}")
        return jsonify({'success': False, 'message': 'Error loading payment history'}), 500

@accounts_bp.route('/edit-profile', methods=['GET', 'POST'])
@login_required
@accounts_required()
def edit_profile():
    """Edit user profile"""
    if request.method == 'POST':
        try:
            # Get current user
            user = current_user
            
            # Update basic info
            if hasattr(user, 'name'):
                user.name = request.form.get('name', user.name)
            if hasattr(user, 'email'):
                user.email = request.form.get('email', user.email)
            if hasattr(user, 'phone'):
                user.phone = request.form.get('phone', user.phone)
            
            # Handle password change
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if current_password and new_password:
                if hasattr(user, 'check_password') and user.check_password(current_password):
                    if new_password == confirm_password:
                        if hasattr(user, 'set_password'):
                            user.set_password(new_password)
                        else:
                            flash('Password change not supported for your account type', 'error')
                            return redirect(url_for('accounts.edit_profile'))
                    else:
                        flash('New passwords do not match', 'error')
                        return redirect(url_for('accounts.edit_profile'))
                else:
                    flash('Current password is incorrect', 'error')
                    return redirect(url_for('accounts.edit_profile'))
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('accounts.accounts_dashboard'))
            
        except Exception as e:
            current_app.logger.error(f"Error updating profile: {str(e)}")
            flash(f'Error updating profile: {str(e)}', 'error')
    
    return render_template('edit_profile.html')

@accounts_bp.route('/reports/export/<format>')
@login_required
@accounts_required()
def export_reports(format):
    """Export reports in different formats"""
    try:
        # Get all fee records with student information
        fee_records_data = safe_execute(lambda: db.session.query(
            FeeRecord, Student
        ).join(Student, FeeRecord.student_id == Student.id)
        .order_by(FeeRecord.last_updated.desc())
        .all()) or []
        
        if format == 'csv':
            # Create CSV data
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'Student ID', 'Roll Number', 'Name', 'Department', 'Semester',
                'Total Amount', 'Paid Amount', 'Balance', 'Last Updated'
            ])
            
            # Write data
            for fee_record, student in fee_records_data:
                writer.writerow([
                    student.id,
                    student.roll_number,
                    student.name,
                    student.department or 'N/A',
                    fee_record.semester,
                    fee_record.total_amount,
                    fee_record.paid_amount,
                    fee_record.balance,
                    fee_record.last_updated.strftime('%Y-%m-%d %H:%M:%S')
                ])
            
            output.seek(0)
            from flask import Response
            response = Response(output.getvalue(), mimetype='text/csv')
            response.headers['Content-Disposition'] = f'attachment; filename=fee_reports_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            return response
            
        elif format == 'excel':
            # Create Excel data (CSV format for simplicity, can be enhanced with openpyxl)
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'Student ID', 'Roll Number', 'Name', 'Department', 'Semester',
                'Total Amount', 'Paid Amount', 'Balance', 'Last Updated', 'Status'
            ])
            
            # Write data
            for fee_record, student in fee_records_data:
                status = 'Paid' if fee_record.balance <= 0 else (
                    'Partial' if fee_record.paid_amount > 0 else 'Unpaid'
                )
                writer.writerow([
                    student.id,
                    student.roll_number,
                    student.name,
                    student.department or 'N/A',
                    fee_record.semester,
                    fee_record.total_amount,
                    fee_record.paid_amount,
                    fee_record.balance,
                    fee_record.last_updated.strftime('%Y-%m-%d %H:%M:%S'),
                    status
                ])
            
            output.seek(0)
            from flask import Response
            response = Response(output.getvalue(), mimetype='text/csv')
            response.headers['Content-Disposition'] = f'attachment; filename=fee_reports_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            return response
            
        elif format == 'pdf':
            # For PDF, return JSON data that can be used to generate PDF on frontend
            report_data = []
            for fee_record, student in fee_records_data:
                status = 'Paid' if fee_record.balance <= 0 else (
                    'Partial' if fee_record.paid_amount > 0 else 'Unpaid'
                )
                report_data.append({
                    'student_id': student.id,
                    'roll_number': student.roll_number,
                    'name': student.name,
                    'department': student.department or 'N/A',
                    'semester': fee_record.semester,
                    'total_amount': fee_record.total_amount,
                    'paid_amount': fee_record.paid_amount,
                    'balance': fee_record.balance,
                    'last_updated': fee_record.last_updated.strftime('%Y-%m-%d %H:%M:%S'),
                    'status': status
                })
            
            return jsonify({
                'success': True,
                'data': report_data,
                'filename': f'fee_reports_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
            })
        
        else:
            return jsonify({'success': False, 'message': 'Unsupported format'}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error exporting reports: {str(e)}")
        return jsonify({'success': False, 'message': 'Error exporting reports'}), 500

@accounts_bp.route('/reports/generate/<report_type>')
@login_required
@accounts_required()
def generate_reports(report_type):
    """Generate different types of reports"""
    try:
        from datetime import timedelta, datetime
        
        if report_type == 'monthly':
            # Monthly report (last 30 days)
            start_date = datetime.utcnow() - timedelta(days=30)
            fee_records = safe_execute(lambda: FeeRecord.query
                                     .filter(FeeRecord.last_updated >= start_date)
                                     .order_by(FeeRecord.last_updated.desc()).all()) or []
            
            # Calculate monthly statistics
            monthly_collected = sum(record.paid_amount for record in fee_records)
            monthly_pending = sum(record.balance for record in fee_records if record.balance > 0)
            monthly_transactions = len(fee_records)
            
            return jsonify({
                'success': True,
                'report_type': 'monthly',
                'period': f'Last 30 days ({start_date.strftime("%Y-%m-%d")} to {datetime.now().strftime("%Y-%m-%d")})',
                'statistics': {
                    'total_collected': monthly_collected,
                    'total_pending': monthly_pending,
                    'total_transactions': monthly_transactions,
                    'average_transaction': monthly_collected / monthly_transactions if monthly_transactions > 0 else 0
                },
                'data': [{
                    'student_id': record.student_id,
                    'semester': record.semester,
                    'total_amount': record.total_amount,
                    'paid_amount': record.paid_amount,
                    'balance': record.balance,
                    'last_updated': record.last_updated.strftime('%Y-%m-%d %H:%M:%S')
                } for record in fee_records]
            })
            
        elif report_type == 'yearly':
            # Yearly report (current year)
            current_year = datetime.utcnow().year
            start_date = datetime(current_year, 1, 1)
            
            fee_records = safe_execute(lambda: FeeRecord.query
                                     .filter(FeeRecord.last_updated >= start_date)
                                     .order_by(FeeRecord.last_updated.desc()).all()) or []
            
            # Calculate yearly statistics
            yearly_collected = sum(record.paid_amount for record in fee_records)
            yearly_pending = sum(record.balance for record in fee_records if record.balance > 0)
            yearly_transactions = len(fee_records)
            
            # Monthly breakdown
            monthly_breakdown = {}
            for record in fee_records:
                month = record.last_updated.strftime('%Y-%m')
                if month not in monthly_breakdown:
                    monthly_breakdown[month] = {'collected': 0, 'pending': 0, 'transactions': 0}
                monthly_breakdown[month]['collected'] += record.paid_amount
                monthly_breakdown[month]['pending'] += record.balance if record.balance > 0 else 0
                monthly_breakdown[month]['transactions'] += 1
            
            return jsonify({
                'success': True,
                'report_type': 'yearly',
                'period': f'Year {current_year}',
                'statistics': {
                    'total_collected': yearly_collected,
                    'total_pending': yearly_pending,
                    'total_transactions': yearly_transactions,
                    'average_transaction': yearly_collected / yearly_transactions if yearly_transactions > 0 else 0
                },
                'monthly_breakdown': monthly_breakdown,
                'data': [{
                    'student_id': record.student_id,
                    'semester': record.semester,
                    'total_amount': record.total_amount,
                    'paid_amount': record.paid_amount,
                    'balance': record.balance,
                    'last_updated': record.last_updated.strftime('%Y-%m-%d %H:%M:%S')
                } for record in fee_records]
            })
            
        elif report_type == 'custom':
            # Custom range report (last 90 days by default)
            start_date = datetime.utcnow() - timedelta(days=90)
            
            fee_records = safe_execute(lambda: FeeRecord.query
                                     .filter(FeeRecord.last_updated >= start_date)
                                     .order_by(FeeRecord.last_updated.desc()).all()) or []
            
            # Calculate custom range statistics
            range_collected = sum(record.paid_amount for record in fee_records)
            range_pending = sum(record.balance for record in fee_records if record.balance > 0)
            range_transactions = len(fee_records)
            
            return jsonify({
                'success': True,
                'report_type': 'custom',
                'period': f'Last 90 days ({start_date.strftime("%Y-%m-%d")} to {datetime.now().strftime("%Y-%m-%d")})',
                'statistics': {
                    'total_collected': range_collected,
                    'total_pending': range_pending,
                    'total_transactions': range_transactions,
                    'average_transaction': range_collected / range_transactions if range_transactions > 0 else 0
                },
                'data': [{
                    'student_id': record.student_id,
                    'semester': record.semester,
                    'total_amount': record.total_amount,
                    'paid_amount': record.paid_amount,
                    'balance': record.balance,
                    'last_updated': record.last_updated.strftime('%Y-%m-%d %H:%M:%S')
                } for record in fee_records]
            })
        
        else:
            return jsonify({'success': False, 'message': 'Unsupported report type'}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error generating reports: {str(e)}")
        return jsonify({'success': False, 'message': 'Error generating reports'}), 500

@accounts_bp.route('/reports')
@login_required
@accounts_required()
def reports():
    """Generate and export financial reports"""
    try:
        # Get real-time data for reports
        total_students = safe_execute(lambda: Student.query.count()) or 0
        total_fee_records = safe_execute(lambda: FeeRecord.query.count()) or 0
        total_faculty = safe_execute(lambda: Faculty.query.count()) or 0
        total_notifications = safe_execute(lambda: Notification.query.count()) or 0
        total_complaints = safe_execute(lambda: Complaint.query.count()) or 0
        total_results = safe_execute(lambda: Result.query.count()) or 0
        
        # Calculate financial summary from fee records
        fee_records = safe_execute(lambda: FeeRecord.query.all()) or []
        total_collected = sum(record.paid_amount for record in fee_records) if fee_records else 0
        total_pending = sum(record.balance for record in fee_records if record.balance > 0) if fee_records else 0
        total_revenue = sum(record.total_amount for record in fee_records) if fee_records else 0
        
        # Calculate fee status counts
        fully_paid = sum(1 for record in fee_records if record.balance <= 0) if fee_records else 0
        partial_payment = sum(1 for record in fee_records if record.paid_amount > 0 and record.balance > 0) if fee_records else 0
        unpaid = sum(1 for record in fee_records if record.paid_amount <= 0) if fee_records else 0
        
        # Get department-wise statistics
        departments = safe_execute(lambda: db.session.query(Student.department, db.func.count(Student.id))
                                 .filter(Student.department.isnot(None))
                                 .group_by(Student.department).all()) or []
        
        # Get semester-wise statistics
        semesters = safe_execute(lambda: db.session.query(Student.semester, db.func.count(Student.id))
                                .filter(Student.semester.isnot(None))
                                .group_by(Student.semester).order_by(Student.semester).all()) or []
        
        # Get recent fee records (last 30 days)
        from datetime import timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_fee_records = safe_execute(lambda: FeeRecord.query
                                         .filter(FeeRecord.last_updated >= thirty_days_ago)
                                         .order_by(FeeRecord.last_updated.desc()).limit(50).all()) or []
        
        return render_template('reports.html',
                             total_students=total_students,
                             total_fee_records=total_fee_records,
                             total_faculty=total_faculty,
                             total_notifications=total_notifications,
                             total_complaints=total_complaints,
                             total_results=total_results,
                             total_collected=total_collected,
                             total_pending=total_pending,
                             total_revenue=total_revenue,
                             fully_paid=fully_paid,
                             partial_payment=partial_payment,
                             unpaid=unpaid,
                             departments=departments,
                             semesters=semesters,
                             recent_fee_records=recent_fee_records)
    except Exception as e:
        current_app.logger.error(f"Error loading reports: {str(e)}")
        flash('Error loading reports.', 'error')
        return redirect(url_for('accounts.accounts_dashboard'))
