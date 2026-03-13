"""
Database Setup Service
Handles database initialization and user management without hardcoded values
"""

from flask import current_app
from app.services.user_service import UserService
from app.extensions import db
from app.models import Admin, Student, Faculty


class DatabaseSetup:
    """Service for database setup and management"""
    
    @staticmethod
    def initialize_database():
        """Initialize database with environment-based configuration"""
        try:
            # Create tables
            db.create_all()
            current_app.logger.info("Database tables created successfully")
            
            # Initialize default admin from environment
            DatabaseSetup._initialize_default_users()
            
            # Sync schema
            DatabaseSetup._ensure_schema()
            
            current_app.logger.info("Database initialization completed")
            return True
            
        except Exception as e:
            current_app.logger.error(f"Database initialization failed: {str(e)}")
            return False
    
    @staticmethod
    def _initialize_default_users():
        """Initialize default users from environment variables"""
        try:
            # Initialize default admin
            admin_result = UserService.initialize_default_admin()
            if admin_result:
                current_app.logger.info(f"Default admin initialized: {admin_result.username}")
            else:
                current_app.logger.warning("Default admin initialization failed")
                
        except Exception as e:
            current_app.logger.error(f"Error initializing default users: {str(e)}")
    
    @staticmethod
    def _ensure_schema():
        """Ensure database schema is up to date"""
        try:
            from sqlalchemy import inspect, text
            
            inspector = inspect(db.engine)
            
            def has_column(table: str, col: str) -> bool:
                try:
                    return any(c.get('name') == col for c in inspector.get_columns(table))
                except Exception:
                    return False
            
            # notifications: notification_type, priority
            if inspector.has_table('notifications'):
                if not has_column('notifications', 'notification_type'):
                    db.session.execute(text("ALTER TABLE notifications ADD COLUMN notification_type VARCHAR(50) DEFAULT 'general'"))
                if not has_column('notifications', 'priority'):
                    db.session.execute(text("ALTER TABLE notifications ADD COLUMN priority VARCHAR(20) DEFAULT 'medium'"))
            
            # faculty: role, password
            if inspector.has_table('faculty'):
                if not has_column('faculty', 'role'):
                    db.session.execute(text("ALTER TABLE faculty ADD COLUMN role VARCHAR(20) DEFAULT 'faculty'"))
                if not has_column('faculty', 'password_hash'):
                    db.session.execute(text("ALTER TABLE faculty ADD COLUMN password_hash VARCHAR(255)"))
            
            # results: created_by
            if inspector.has_table('results'):
                if not has_column('results', 'created_by'):
                    db.session.execute(text("ALTER TABLE results ADD COLUMN created_by INTEGER"))
            
            # telegram_user_mappings: student_id nullable, add verified
            if inspector.has_table('telegram_user_mappings'):
                if not has_column('telegram_user_mappings', 'verified'):
                    db.session.execute(text("ALTER TABLE telegram_user_mappings ADD COLUMN verified BOOLEAN DEFAULT 0"))
            
            # admins: is_active
            if inspector.has_table('admins'):
                if not has_column('admins', 'is_active'):
                    db.session.execute(text("ALTER TABLE admins ADD COLUMN is_active BOOLEAN DEFAULT 1"))
            
            db.session.commit()
            current_app.logger.info("Database schema sync completed")
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.warning(f"Schema sync failed: {str(e)}")
    
    @staticmethod
    def create_user_from_config(user_type='admin'):
        """Create user from configuration"""
        try:
            config_map = {
                'admin': {
                    'username': current_app.config.get('DEFAULT_ADMIN_USERNAME'),
                    'email': current_app.config.get('DEFAULT_ADMIN_EMAIL'),
                    'password': current_app.config.get('DEFAULT_ADMIN_PASSWORD'),
                    'role': current_app.config.get('DEFAULT_ADMIN_ROLE', 'admin')
                }
            }
            
            if user_type not in config_map:
                return {'success': False, 'message': f'Unknown user type: {user_type}'}
            
            config = config_map[user_type]
            
            # Validate configuration
            if not all(config.values()):
                return {'success': False, 'message': f'Missing configuration for {user_type} user'}
            
            # Create user
            result = UserService.create_user(
                username=config['username'],
                email=config['email'],
                password=config['password'],
                role=config['role'],
                is_active=True
            )
            
            return result
            
        except Exception as e:
            current_app.logger.error(f"Error creating user from config: {str(e)}")
            return {'success': False, 'message': f'Error creating user: {str(e)}'}
    
    @staticmethod
    def reset_admin_password(new_password=None):
        """Reset admin password"""
        try:
            admin_username = current_app.config.get('DEFAULT_ADMIN_USERNAME', 'admin')
            
            if not new_password:
                new_password = current_app.config.get('DEFAULT_ADMIN_PASSWORD')
            
            if not new_password:
                return {'success': False, 'message': 'No new password provided'}
            
            admin = UserService.get_user_by_username(admin_username)
            if not admin:
                return {'success': False, 'message': 'Admin user not found'}
            
            result = UserService.reset_password(admin.id, new_password)
            return result
            
        except Exception as e:
            current_app.logger.error(f"Error resetting admin password: {str(e)}")
            return {'success': False, 'message': f'Error resetting password: {str(e)}'}
    
    @staticmethod
    def get_database_info():
        """Get database information"""
        try:
            info = {
                'users': {
                    'total': Admin.query.count(),
                    'admin': Admin.query.filter_by(role='admin').count(),
                    'faculty': Admin.query.filter_by(role='faculty').count(),
                    'accounts': Admin.query.filter_by(role='accounts').count(),
                    'active': Admin.query.filter_by(is_active=True).count()
                },
                'students': Student.query.count() if Student.query else 0,
                'faculty_records': Faculty.query.count() if Faculty.query else 0
            }
            
            return {'success': True, 'info': info}
            
        except Exception as e:
            current_app.logger.error(f"Error getting database info: {str(e)}")
            return {'success': False, 'message': f'Error getting database info: {str(e)}'}
    
    @staticmethod
    def cleanup_inactive_users():
        """Clean up inactive users"""
        try:
            inactive_users = Admin.query.filter_by(is_active=False).all()
            count = 0
            
            for user in inactive_users:
                db.session.delete(user)
                count += 1
            
            db.session.commit()
            current_app.logger.info(f"Cleaned up {count} inactive users")
            
            return {'success': True, 'message': f'Cleaned up {count} inactive users'}
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error cleaning up inactive users: {str(e)}")
            return {'success': False, 'message': f'Error cleaning up users: {str(e)}'}
    
    @staticmethod
    def validate_configuration():
        """Validate environment configuration"""
        try:
            required_vars = [
                'DEFAULT_ADMIN_USERNAME',
                'DEFAULT_ADMIN_EMAIL', 
                'DEFAULT_ADMIN_PASSWORD',
                'DEFAULT_ADMIN_ROLE'
            ]
            
            missing_vars = []
            for var in required_vars:
                if not current_app.config.get(var):
                    missing_vars.append(var)
            
            if missing_vars:
                return {
                    'success': False,
                    'message': f'Missing required environment variables: {", ".join(missing_vars)}'
                }
            
            # Validate role
            valid_roles = ['admin', 'faculty', 'accounts']
            role = current_app.config.get('DEFAULT_ADMIN_ROLE')
            if role not in valid_roles:
                return {
                    'success': False,
                    'message': f'Invalid role. Must be one of: {", ".join(valid_roles)}'
                }
            
            return {'success': True, 'message': 'Configuration is valid'}
            
        except Exception as e:
            current_app.logger.error(f"Error validating configuration: {str(e)}")
            return {'success': False, 'message': f'Configuration validation error: {str(e)}'}
