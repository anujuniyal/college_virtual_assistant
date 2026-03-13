"""
User Management Service
Handles all user operations through database only
"""

from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models import Admin
import os


class UserService:
    """Service for managing users through database"""
    
    @staticmethod
    def create_user(username, email, password, role, is_active=True):
        """Create a new user in the database"""
        try:
            # Check if user already exists
            existing_user = Admin.query.filter(
                (Admin.username == username) | (Admin.email == email)
            ).first()
            
            if existing_user:
                if existing_user.username == username:
                    return {'success': False, 'message': 'Username already exists'}
                else:
                    return {'success': False, 'message': 'Email already exists'}
            
            # Create new user
            user = Admin(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                role=role,
                is_active=is_active
            )
            
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
        """Authenticate user against faculty table only for dashboard login"""
        try:
            # Only check Faculty table for dashboard authentication
            from app.models import Faculty
            faculty = Faculty.query.filter_by(email=username).first()
            
            if not faculty:
                return {'success': False, 'message': 'Invalid credentials'}
            
            if not faculty.check_password(password):
                return {'success': False, 'message': 'Invalid credentials'}
            
            return {
                'success': True,
                'message': 'Authentication successful',
                'user': faculty
            }
            
        except Exception as e:
            current_app.logger.error(f"Authentication error: {str(e)}")
            return {'success': False, 'message': 'Authentication failed'}
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID"""
        try:
            return Admin.query.get(user_id)
        except Exception as e:
            current_app.logger.error(f"Error getting user: {str(e)}")
            return None
    
    @staticmethod
    def get_user_by_username(username):
        """Get user by username or email"""
        try:
            return Admin.query.filter(
                (Admin.username == username) | (Admin.email == username)
            ).first()
        except Exception as e:
            current_app.logger.error(f"Error getting user: {str(e)}")
            return None
    
    @staticmethod
    def update_user(user_id, **kwargs):
        """Update user information"""
        try:
            user = Admin.query.get(user_id)
            if not user:
                return {'success': False, 'message': 'User not found'}
            
            # Update allowed fields
            allowed_fields = ['username', 'email', 'role', 'is_active']
            for field, value in kwargs.items():
                if field in allowed_fields:
                    setattr(user, field, value)
            
            # Handle password update separately
            if 'password' in kwargs:
                user.password_hash = generate_password_hash(kwargs['password'])
            
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
        """Delete user from database"""
        try:
            user = Admin.query.get(user_id)
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
        """Get all users"""
        try:
            return Admin.query.order_by(Admin.created_at.desc()).all()
        except Exception as e:
            current_app.logger.error(f"Error getting users: {str(e)}")
            return []
    
    @staticmethod
    def get_users_by_role(role):
        """Get users by role"""
        try:
            return Admin.query.filter_by(role=role).order_by(Admin.created_at.desc()).all()
        except Exception as e:
            current_app.logger.error(f"Error getting users by role: {str(e)}")
            return []
    
    @staticmethod
    def initialize_default_admin():
        """Initialize default admin from environment variables"""
        try:
            admin_username = current_app.config['DEFAULT_ADMIN_USERNAME']
            admin_email = current_app.config['DEFAULT_ADMIN_EMAIL']
            admin_password = current_app.config['DEFAULT_ADMIN_PASSWORD']
            admin_role = current_app.config['DEFAULT_ADMIN_ROLE']
            
            # Check if admin already exists
            existing_admin = Admin.query.filter_by(username=admin_username).first()
            if existing_admin:
                current_app.logger.info(f"Default admin {admin_username} already exists")
                return existing_admin
            
            # Create default admin
            result = UserService.create_user(
                username=admin_username,
                email=admin_email,
                password=admin_password,
                role=admin_role,
                is_active=True
            )
            
            if result['success']:
                current_app.logger.info(f"Default admin {admin_username} created successfully")
                return UserService.get_user_by_username(admin_username)
            else:
                current_app.logger.error(f"Failed to create default admin: {result['message']}")
                return None
                
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
        """Change user password"""
        try:
            user = Admin.query.get(user_id)
            if not user:
                return {'success': False, 'message': 'User not found'}
            
            # Verify old password
            if not user.check_password(old_password):
                return {'success': False, 'message': 'Current password is incorrect'}
            
            # Update password
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            
            return {'success': True, 'message': 'Password changed successfully'}
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error changing password: {str(e)}")
            return {'success': False, 'message': 'Error changing password'}
    
    @staticmethod
    def reset_password(user_id, new_password):
        """Reset user password (admin function)"""
        try:
            user = Admin.query.get(user_id)
            if not user:
                return {'success': False, 'message': 'User not found'}
            
            # Update password
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            
            return {'success': True, 'message': 'Password reset successfully'}
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error resetting password: {str(e)}")
            return {'success': False, 'message': 'Error resetting password'}
