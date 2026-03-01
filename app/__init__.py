"""
Flask Application Factory Pattern
"""

from app.factory import create_app

# Export the create_app function
__all__ = ['create_app']
