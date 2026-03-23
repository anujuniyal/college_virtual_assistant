"""
User Management Service
Handles all user operations through database only
"""

from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models import Faculty
import os


class UserService:
    """Service for managing users through database"""
    
    @staticmethod
    def create_user(username, email, password, role, is_active=True):
        """Create a new user in the Faculty table"""
        try:
            # Check if user already exists in Faculty table
            existing_user = Faculty.query.filter(
                (Faculty.email == email)
            ).first()
            
            if existing_user:
                return {'success': False, 'message': 'Email already exists'}
            
            # Create new faculty user
            user = Faculty(
                name=username,
                email=email,
                department='Administration',
                role=role,
                phone='N/A'
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            return {
                'success': True, 
                'message': f'User {username} created successfully',
                'user_id': user.id
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating user: {str(e)}")
            return {'success': False, 'message': f'Error creating user: {str(e)}'}
    
    @staticmethod
    def authenticate_user(username, password):
        """Authenticate user against Admin and Faculty tables"""
        try:
            from app.models import Admin, Faculty
            
            # First check Admin table for admin users
            admin = Admin.query.filter_by(email=username).first()
            if admin and admin.check_password(password):
                return {
                    'success': True,
                    'message': 'Authentication successful',
                    'user': admin
                }
            
            # Then check Faculty table for faculty/accounts users
            faculty = Faculty.query.filter_by(email=username).first()
            if faculty and faculty.check_password(password):
                return {
                    'success': True,
                    'message': 'Authentication successful',
                    'user': faculty
                }
            
            return {'success': False, 'message': 'Invalid credentials'}
            
        except Exception as e:
            current_app.logger.error(f"Authentication error: {str(e)}")
            return {'success': False, 'message': 'Authentication failed'}
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID from Admin and Faculty tables"""
        try:
            from app.models import Admin, Faculty
            
            # First check Admin table
            user = Admin.query.get(user_id)
            if user:
                return user
            
            # Then check Faculty table
            user = Faculty.query.get(user_id)
            return user
            
        except Exception as e:
            current_app.logger.error(f"Error getting user: {str(e)}")
            return None
    
    @staticmethod
    def get_user_by_username(username):
        """Get user by email from Admin and Faculty tables"""
        try:
            from app.models import Admin, Faculty
            
            # First check Admin table
            user = Admin.query.filter_by(email=username).first()
            if user:
                return user
            
            # Then check Faculty table
            user = Faculty.query.filter_by(email=username).first()
            return user
            
        except Exception as e:
            current_app.logger.error(f"Error getting user: {str(e)}")
            return None
    
    @staticmethod
    def update_user(user_id, **kwargs):
        """Update user information in Faculty table"""
        try:
            user = Faculty.query.get(user_id)
            if not user:
                return {'success': False, 'message': 'User not found'}
            
            # Update allowed fields
            allowed_fields = ['name', 'email', 'role', 'department', 'phone']
            for field, value in kwargs.items():
                if field in allowed_fields:
                    setattr(user, field, value)
            
            # Handle password update separately
            if 'password' in kwargs:
                user.set_password(kwargs['password'])
            
            db.session.commit()
            
            return {
                'success': True,
                'message': 'User updated successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating user: {str(e)}")
            return {'success': False, 'message': f'Error updating user: {str(e)}'}
    
    @staticmethod
    def delete_user(user_id):
        """Delete user from Faculty table"""
        try:
            user = Faculty.query.get(user_id)
            if not user:
                return {'success': False, 'message': 'User not found'}
            
            db.session.delete(user)
            db.session.commit()
            
            return {
                'success': True,
                'message': 'User deleted successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting user: {str(e)}")
            return {'success': False, 'message': f'Error deleting user: {str(e)}'}
    
    @staticmethod
    def get_all_users():
        """Get all users from Faculty table"""
        try:
            return Faculty.query.order_by(Faculty.created_at.desc()).all()
        except Exception as e:
            current_app.logger.error(f"Error getting users: {str(e)}")
            return []
    
    @staticmethod
    def get_users_by_role(role):
        """Get users by role from Faculty table"""
        try:
            return Faculty.query.filter_by(role=role).order_by(Faculty.created_at.desc()).all()
        except Exception as e:
            current_app.logger.error(f"Error getting users by role: {str(e)}")
            return []
    
    @staticmethod
    def initialize_default_admin():
        """Initialize default admin in Faculty table"""
        try:
            admin_email = current_app.config['DEFAULT_ADMIN_EMAIL']
            admin_password = current_app.config['DEFAULT_ADMIN_PASSWORD']
            admin_role = current_app.config['DEFAULT_ADMIN_ROLE']
            
            # Check if admin already exists in Faculty table
            existing_admin = Faculty.query.filter_by(email=admin_email).first()
            if existing_admin:
                current_app.logger.info(f"Default admin {admin_email} already exists in Faculty table")
                return existing_admin
            
            # Create default admin in Faculty table
            admin = Faculty(
                name='Default Admin',
                email=admin_email,
                department='Administration',
                role=admin_role,
                phone='N/A'
            )
            admin.set_password(admin_password)
            
            db.session.add(admin)
            db.session.commit()
            
            current_app.logger.info(f"Default admin {admin_email} created successfully in Faculty table")
            return admin
                
        except Exception as e:
            current_app.logger.error(f"Error initializing default admin: {str(e)}")
            return None
    
    @staticmethod
    def validate_user_data(username, email, password, role):
        """Validate user data"""
        errors = []
        
        # Validate username
        if not username or len(username) < 3:
            errors.append("Username must be at least 3 characters long")
        elif not username.replace('_', '').replace('-', '').isalnum():
            errors.append("Username can only contain letters, numbers, underscores, and hyphens")
        
        # Validate email
        if not email or '@' not in email:
            errors.append("Valid email address is required")
        
        # Validate password
        if not password or len(password) < 6:
            errors.append("Password must be at least 6 characters long")
        
        # Validate role
        valid_roles = ['admin', 'faculty', 'accounts']
        if not role or role not in valid_roles:
            errors.append(f"Role must be one of: {', '.join(valid_roles)}")
        
        return errors
    
    @staticmethod
    def change_password(user_id, old_password, new_password):
        """Change user password in Faculty table"""
        try:
            user = Faculty.query.get(user_id)
            if not user:
                return {'success': False, 'message': 'User not found'}
            
            # Verify old password
            if not user.check_password(old_password):
                return {'success': False, 'message': 'Current password is incorrect'}
            
            # Update password
            user.set_password(new_password)
            db.session.commit()
            
            return {'success': True, 'message': 'Password changed successfully'}
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error changing password: {str(e)}")
            return {'success': False, 'message': 'Error changing password'}
    
    @staticmethod
    def reset_password(user_id, new_password):
        """Reset user password in Faculty table (admin function)"""
        try:
            user = Faculty.query.get(user_id)
            if not user:
                return {'success': False, 'message': 'User not found'}
            
            # Update password
            user.set_password(new_password)
            db.session.commit()
            
            return {'success': True, 'message': 'Password reset successfully'}
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error resetting password: {str(e)}")
            return {'success': False, 'message': 'Error resetting password'}
