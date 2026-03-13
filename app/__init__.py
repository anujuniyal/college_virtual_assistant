"""
Flask Application Factory Pattern
"""

from app.factory import create_app
from app.extensions import db, login_manager, mail

# Re-export commonly used objects for tests and app entrypoints
__all__ = ['create_app', 'db', 'login_manager', 'mail']
