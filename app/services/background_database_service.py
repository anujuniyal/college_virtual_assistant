"""
Background Database Service - Works outside Flask application context
"""
import logging
import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Set up logger for background operations
logger = logging.getLogger(__name__)


class BackgroundDatabaseService:
    """Database service that works in background threads without Flask context"""
    
    def __init__(self):
        # Get database URL from environment
        self.database_url = os.environ.get('DATABASE_URL')
        if not self.database_url:
            logger.error("DATABASE_URL not found in environment")
            return
        
        # Create engine and session for background operations
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    @contextmanager
    def get_db_session(self):
        """Context manager for database sessions in background threads"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database operation failed: {str(e)}")
            raise
        finally:
            session.close()
    
    def mark_otp_used(self, email: str, otp_code: str) -> bool:
        """Mark OTP as used in database"""
        try:
            with self.get_db_session() as session:
                from app.models import OTP
                
                otp = session.query(OTP).filter_by(
                    email=email,
                    otp_code=otp_code,
                    used=False
                ).order_by(OTP.created_at.desc()).first()
                
                if otp:
                    otp.used = True
                    session.commit()
                    logger.info(f"OTP marked as used for {email}")
                    return True
                else:
                    logger.warning(f"No active OTP found for {email}")
                    return False
                    
        except SQLAlchemyError as e:
            logger.error(f"Database error marking OTP used: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error marking OTP used: {str(e)}")
            return False


# Singleton instance for background threads
_background_database_service = None


def get_background_database_service():
    """Get or create background database service instance"""
    global _background_database_service
    if _background_database_service is None:
        _background_database_service = BackgroundDatabaseService()
    return _background_database_service


def mark_otp_used_background(email: str, otp_code: str) -> bool:
    """
    Mark OTP as used from background thread without Flask context
    This is the main function to use from background threads
    """
    service = get_background_database_service()
    return service.mark_otp_used(email, otp_code)
