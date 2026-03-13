from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user, UserMixin
from app.extensions import db
from app.models import Admin, Student, Faculty
from app.services.user_service import UserService
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page - Faculty table authentication only"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Use UserService for faculty-only authentication
        auth_result = UserService.authenticate_user(username, password)
        
        if auth_result['success']:
            user = auth_result['user']
            login_user(user)
            flash('Login successful!', 'success')
            
            # Get user role from faculty table
            if hasattr(user, 'role'):
                user_role = user.role
            elif hasattr(user, 'user_role'):
                user_role = user.user_role
            else:
                user_role = 'faculty'  # Default to faculty for safety
            
            # Redirect based on user role
            if user_role == 'admin':
                return redirect(url_for('admin.admin_dashboard_main'))
            elif user_role == 'faculty':
                return redirect(url_for('faculty.faculty_dashboard'))
            elif user_role == 'accounts':
                return redirect(url_for('accounts.accounts_dashboard'))
            else:
                return redirect(url_for('faculty.faculty_dashboard'))  # Default to faculty
        else:
            flash(auth_result['message'], 'error')
    
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register new user"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'student')
        
        # Check if user already exists in appropriate table
        if role == 'student':
            existing_user = Student.query.filter_by(roll_number=request.form.get('roll_number', '')).first()
        elif role == 'faculty':
            existing_user = Faculty.query.filter_by(email=email).first()
        else:
            existing_user = Admin.query.filter_by(username=username).first()

        if existing_user:
            flash('User already exists with these details', 'error')
            return render_template('register.html')

        # Create new user based on role
        if role == 'student':
            student_name = request.form.get('name') or username
            new_user = Student(
                name=student_name,
                email=email,
                phone=request.form.get('phone', ''),
                department=request.form.get('department', ''),
                semester=int(request.form.get('semester', 1) or 1),
                roll_number=request.form.get('roll_number', '')
            )
        elif role == 'faculty':
            faculty_name = request.form.get('name') or username
            new_user = Faculty(
                name=faculty_name,
                email=email,
                phone=request.form.get('phone', ''),
                department=request.form.get('department', ''),
                consultation_time=request.form.get('consultation_time', '')
            )
        else:
            new_user = Admin(
                username=username,
                email=email,
                role=role
            )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')
