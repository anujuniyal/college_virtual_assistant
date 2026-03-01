"""
Cleanup Service for Auto-deletion
"""
from datetime import datetime
from flask import current_app
from app.extensions import db
from app.models import Notification, Result, OTP


class CleanupService:
    """Auto-cleanup service"""
    
    @staticmethod
    def cleanup_expired_notifications():
        """Delete expired notifications"""
        try:
            expired_count = Notification.query.filter(
                Notification.expires_at < datetime.utcnow()
            ).delete()
            db.session.commit()
            return expired_count
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error cleaning up notifications: {str(e)}")
            return 0
    
    @staticmethod
    def cleanup_expired_results():
        """Delete results after semester end"""
        try:
            expired_count = Result.query.filter(
                Result.semester_end_date < datetime.utcnow()
            ).delete()
            db.session.commit()
            return expired_count
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error cleaning up results: {str(e)}")
            return 0
    
    @staticmethod
    def cleanup_expired_otps():
        """Delete expired OTPs"""
        try:
            expired_count = OTP.query.filter(
                OTP.expires_at < datetime.utcnow()
            ).delete()
            db.session.commit()
            return expired_count
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error cleaning up OTPs: {str(e)}")
            return 0
    
    @staticmethod
    def run_all_cleanup():
        """Run all cleanup tasks"""
        notifications = CleanupService.cleanup_expired_notifications()
        results = CleanupService.cleanup_expired_results()
        otps = CleanupService.cleanup_expired_otps()
        
        return {
            'notifications': notifications,
            'results': results,
            'otps': otps
        }
    
    @staticmethod
    def run_cleanup_on_startup():
        """Run cleanup on application startup"""
        try:
            cleanup_results = CleanupService.run_all_cleanup()
            try:
                current_app.logger.info(f"Cleanup on startup: {cleanup_results}")
            except:
                print(f"Cleanup on startup: {cleanup_results}")
        except Exception as e:
            try:
                current_app.logger.error(f"Error during startup cleanup: {str(e)}")
            except:
                print(f"Error during startup cleanup: {str(e)}")
