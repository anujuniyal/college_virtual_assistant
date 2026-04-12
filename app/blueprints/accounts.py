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
            
            # Check accounts access - allow admin, faculty, and accounts roles
            if user_role not in ['admin', 'faculty', 'accounts']:
                flash('Access denied. Accounts privileges required.', 'error')
                return redirect(url_for('auth.login'))
            
            # Check write access for fee operations
            if write_access and user_role not in ['accounts']:
                flash('Write access required for fee operations. Contact admin for accounts role.', 'error')
                return redirect(url_for('auth.login'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@accounts_bp.route('/dashboard')
@login_required
@accounts_required()
def accounts_dashboard():
    """Accounts dashboard with financial access"""
    return redirect(url_for('accounts.students_fees_dashboard'))

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
        
        return render_template('students_fees_standalone.html',
                             students=students_with_fees,
                             pagination=students_pagination,
                             page=page,
                             total_students=len(students_with_fees),
                             fully_paid_count=fully_paid_count,
                             partial_payment_count=partial_payment_count,
                             unpaid_count=unpaid_count)
    
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

@accounts_bp.route('/billing')
@login_required
@accounts_required()
def billing():
    """Billing and financial management"""
    try:
        # Get billing data
        total_students = safe_execute(Student.query.count) or 0
        total_faculty = safe_execute(Faculty.query.count) or 0
        
        return render_template('billing.html',
                             total_students=total_students,
                             total_faculty=total_faculty)
    except Exception as e:
        flash('Error loading billing.', 'error')
        return redirect(url_for('accounts.manage_accounts'))

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
