"""
Flask Extensions
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'
mail = Mail()


@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login (supports both Admin and Faculty tables)"""
    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        return None

    from sqlalchemy.orm.exc import NoResultFound

    try:
        # Import here to avoid circular imports at app startup.
        from app.models import Admin, Faculty

        # First try Faculty table (primary for dashboard access)
        user = db.session.get(Faculty, user_id_int)
        if user:
            return user

        # Fallback to Admin table for backward compatibility
        user = db.session.get(Admin, user_id_int)
        if user:
            return user

        return None

    except Exception:
        # Returning None lets Flask-Login treat the session as anonymous.
        return None
