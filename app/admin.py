"""
Flask-Admin Configuration with RBAC
"""
from datetime import datetime, timedelta

from flask import redirect, url_for, request, flash
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, login_required
from wtforms import PasswordField

from app.extensions import db
from app.models import (
    Admin as AdminModel,
    Student,
    Notification,
    Result,
    FeeRecord,
    Faculty,
    Complaint,
    ChatbotQA,
)
from app.services.weekly_report_service import WeeklyReportService


class SecureAdminIndexView(AdminIndexView):
    """Secure admin index view"""
    
    @expose('/')
    @login_required
    def index(self):
        """Admin dashboard"""
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        return redirect(url_for('admin_dashboard'))


class SecureModelView(ModelView):
    """Base secure model view with RBAC"""
    
    def is_accessible(self):
        """Check if user can access this view"""
        if not current_user.is_authenticated:
            return False
        
        # Admin has full access
        if current_user.role == 'admin':
            return True
        
        # Role-based access
        model_name = self.model.__name__
        
        if current_user.role == 'faculty':
            # Faculty can access: Results, own profile, Notifications, Students
            return model_name in ['Result', 'Notification', 'Admin', 'Student']
        
        if current_user.role == 'accounts':
            # Accounts can access: FeeRecord, Notifications, Students
            return model_name in ['FeeRecord', 'Notification', 'Student']
        
        return False
    
    def inaccessible_callback(self, name, **kwargs):
        """Redirect if access denied"""
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('admin_dashboard'))


class FacultyStudentView(SecureModelView):
    """Faculty-specific student view (read-only)"""
    column_list = ['roll_number', 'name', 'phone', 'email', 'department', 'semester']
    column_searchable_list = ['roll_number', 'name', 'phone', 'email']
    column_filters = ['department', 'semester']
    can_create = False
    can_edit = False
    can_delete = False
    can_export = True
    
    def is_accessible(self):
        """Only faculty can access"""
        return current_user.is_authenticated and current_user.role == 'faculty'


class AccountsStudentView(SecureModelView):
    """Accounts-specific student view"""
    column_list = ['roll_number', 'name', 'phone', 'email', 'department', 'semester']
    column_searchable_list = ['roll_number', 'name', 'phone', 'email']
    column_filters = ['department', 'semester']
    can_create = False
    can_edit = False
    can_delete = False
    can_export = True
    
    def is_accessible(self):
        """Only accounts can access"""
        return current_user.is_authenticated and current_user.role == 'accounts'


class StudentView(SecureModelView):
    """Student model view"""
    column_list = ['roll_number', 'name', 'phone', 'email', 'department', 'semester', 'created_at']
    column_searchable_list = ['roll_number', 'name', 'phone', 'email']
    column_filters = ['department', 'semester']
    form_columns = ['roll_number', 'name', 'phone', 'email', 'department', 'semester']
    can_create = True
    can_edit = True
    can_delete = True
    can_export = True


class FacultyNotificationView(SecureModelView):
    """Faculty-specific notification view"""
    column_list = ['title', 'created_at', 'expires_at', 'created_by']
    column_searchable_list = ['title', 'content']
    form_columns = ['title', 'content', 'file_url', 'link_url', 'expires_at']
    can_create = True
    can_edit = True
    can_delete = True
    
    def is_accessible(self):
        """Only faculty can access"""
        return current_user.is_authenticated and current_user.role == 'faculty'
    
    def on_model_change(self, form, model, is_created):
        """Set expiry date and created_by"""
        if is_created and not model.expires_at:
            model.expires_at = datetime.utcnow() + timedelta(days=7)
        if is_created:
            model.created_by = current_user.id


class AccountsNotificationView(SecureModelView):
    """Accounts-specific notification view"""
    column_list = ['title', 'created_at', 'expires_at', 'created_by']
    column_searchable_list = ['title', 'content']
    form_columns = ['title', 'content', 'file_url', 'link_url', 'expires_at']
    can_create = True
    can_edit = True
    can_delete = True
    
    def is_accessible(self):
        """Only accounts can access"""
        return current_user.is_authenticated and current_user.role == 'accounts'
    
    def on_model_change(self, form, model, is_created):
        """Set expiry date and created_by"""
        if is_created and not model.expires_at:
            model.expires_at = datetime.utcnow() + timedelta(days=7)
        if is_created:
            model.created_by = current_user.id


class NotificationView(SecureModelView):
    """Notification model view"""
    column_list = ['title', 'created_at', 'expires_at', 'created_by']
    column_searchable_list = ['title', 'content']
    form_columns = ['title', 'content', 'file_url', 'link_url', 'expires_at']
    can_create = True
    can_edit = True
    can_delete = True
    
    def on_model_change(self, form, model, is_created):
        """Set expiry date if not provided"""
        if is_created and not model.expires_at:
            model.expires_at = datetime.utcnow() + timedelta(days=7)
        if is_created:
            model.created_by = current_user.id


class ResultView(SecureModelView):
    """Result model view"""
    column_list = ['student', 'semester', 'subject', 'marks', 'grade', 'declared_at', 'semester_end_date']
    column_searchable_list = ['subject']
    column_filters = ['semester', 'grade']
    form_columns = ['student', 'semester', 'subject', 'marks', 'grade', 'semester_end_date']
    can_create = True
    can_edit = True
    can_delete = True
    can_export = True
    
    def on_model_change(self, form, model, is_created):
        """Set declared_at and semester_end_date"""
        if is_created:
            model.declared_at = datetime.utcnow()
            if not model.semester_end_date:
                # Default: 4 months from now (semester end)
                model.semester_end_date = datetime.utcnow() + timedelta(days=120)


class FeeRecordView(SecureModelView):
    """Fee record model view"""
    column_list = ['student', 'semester', 'total_amount', 'paid_amount', 'balance_amount', 'last_updated']
    column_searchable_list = []
    column_filters = ['semester']
    form_columns = ['student', 'semester', 'total_amount', 'paid_amount']
    can_create = True
    can_edit = True
    can_delete = True
    can_export = True
    
    def on_model_change(self, form, model, is_created):
        """Calculate balance"""
        model.balance_amount = model.total_amount - model.paid_amount


class FacultyView(SecureModelView):
    """Faculty model view"""
    column_list = ['name', 'email', 'department', 'consultation_time', 'phone']
    column_searchable_list = ['name', 'email', 'department']
    column_filters = ['department']
    form_columns = ['name', 'email', 'department', 'consultation_time', 'phone']
    can_create = True
    can_edit = True
    can_delete = True


class ComplaintView(SecureModelView):
    """Complaint model view"""
    column_list = ['student', 'category', 'status', 'created_at']
    column_searchable_list = ['category', 'description']
    column_filters = ['category', 'status']
    form_columns = ['student', 'category', 'description', 'status']
    can_create = True
    can_edit = True
    can_delete = True
    can_export = True


class ChatbotQAView(SecureModelView):
    """Chatbot Q&A view"""
    column_list = ['question', 'answer', 'category', 'created_at']
    column_searchable_list = ['question', 'answer']
    column_filters = ['category']
    form_columns = ['question', 'answer', 'category']
    can_create = True
    can_edit = True
    can_delete = True
    can_export = True


# ChatbotUnknownView removed - model doesn't exist


class AdminModelView(SecureModelView):
    """Admin user view (only for admin role)"""
    column_list = ['username', 'email', 'role', 'created_at']
    column_searchable_list = ['username', 'email']
    column_filters = ['role']
    form_columns = ['username', 'email', 'password', 'role']
    form_extra_fields = {
        'password': PasswordField('Password')
    }
    can_create = True
    can_edit = True
    can_delete = True
    
    def is_accessible(self):
        """Only admin can access admin users"""
        return current_user.is_authenticated and current_user.role == 'admin'
    
    def on_model_change(self, form, model, is_created):
        """Handle password hashing"""
        if hasattr(form, 'password') and form.password.data:
            model.set_password(form.password.data)


def init_admin(app):
    """Initialize Flask-Admin"""
    admin = Admin(
        app,
        name='College Virtual Assistant Admin',
        index_view=SecureAdminIndexView(),
        endpoint='flask_admin',
        url='/flask-admin'
    )
    
    # Add views
    admin.add_view(StudentView(Student, db.session, name='Students', category='Data'))
    admin.add_view(FacultyView(Faculty, db.session, name='Faculty', category='Data'))
    admin.add_view(AdminModelView(AdminModel, db.session, name='Admin Users', category='Administration'))
    admin.add_view(NotificationView(Notification, db.session, name='Notifications', category='Services'))
    admin.add_view(ResultView(Result, db.session, name='Results', category='Services'))
    admin.add_view(FeeRecordView(FeeRecord, db.session, name='Fee Records', category='Services'))
    admin.add_view(ComplaintView(Complaint, db.session, name='Complaints', category='Services'))
    admin.add_view(ChatbotQAView(ChatbotQA, db.session, name='Chatbot Q&A', category='Chatbot'))
    # Note: ChatbotUnknown model doesn't exist - view removed
    
    # Add custom route for weekly report
    @app.route('/admin/generate-weekly-report')
    @login_required
    def generate_weekly_report():
        """Generate weekly report"""
        if current_user.role != 'admin':
            flash('Only admins can generate reports.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        try:
            csv_path, visitor_csv_path = WeeklyReportService.generate_weekly_report()
            if csv_path and visitor_csv_path:
                flash(f'Weekly report generated successfully. CSVs saved to: {csv_path} and {visitor_csv_path}', 'success')
            elif csv_path:
                flash(f'Weekly report generated successfully. CSV saved to: {csv_path}', 'success')
            else:
                flash('Weekly report generated successfully (no data to export)', 'success')
        except Exception as e:
            flash(f'Error generating report: {str(e)}', 'error')
        
        return redirect(url_for('admin_dashboard'))
