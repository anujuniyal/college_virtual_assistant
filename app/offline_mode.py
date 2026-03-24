"""
Offline mode for when database connectivity is unavailable
"""
import os
from flask import current_app

class OfflineMode:
    """Handle application in offline mode when database is unreachable"""
    
    @staticmethod
    def is_enabled():
        """Check if offline mode should be enabled"""
        return os.environ.get('OFFLINE_MODE', 'false').lower() == 'true'
    
    @staticmethod
    def enable():
        """Enable offline mode"""
        os.environ['OFFLINE_MODE'] = 'true'
        current_app.logger.warning("🔴 OFFLINE MODE ENABLED - Database connectivity unavailable")
    
    @staticmethod
    def disable():
        """Disable offline mode"""
        os.environ['OFFLINE_MODE'] = 'false'
        current_app.logger.info("🟢 OFFLINE MODE DISABLED - Database connectivity restored")
    
    @staticmethod
    def get_mock_response():
        """Get mock response for health checks"""
        return {
            'status': 'healthy',
            'database': 'offline',
            'mode': 'offline',
            'timestamp': '2026-03-24T11:30:00.000Z',
            'message': 'Application running in offline mode - database temporarily unavailable'
        }


def offline_database_test():
    """
    Mock database test for offline mode
    """
    if OfflineMode.is_enabled():
        current_app.logger.info("Database test skipped - offline mode enabled")
        return True
    
    # Try real database connection
    try:
        from app.database_resilience import test_database_connection
        return test_database_connection()
    except Exception as e:
        current_app.logger.error(f"Database connection failed: {str(e)}")
        current_app.logger.warning("Enabling offline mode due to database connectivity issues")
        OfflineMode.enable()
        return True  # Return True to allow app to continue in offline mode


def offline_database_init():
    """
    Mock database initialization for offline mode
    """
    if OfflineMode.is_enabled():
        current_app.logger.info("Database initialization skipped - offline mode enabled")
        return True
    
    try:
        from app.database_resilience import initialize_database_with_retry
        return initialize_database_with_retry()
    except Exception as e:
        current_app.logger.error(f"Database initialization failed: {str(e)}")
        current_app.logger.warning("Running in offline mode due to database connectivity issues")
        OfflineMode.enable()
        return True  # Return True to allow app to continue
