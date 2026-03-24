"""
Database resilience utilities for handling network connectivity issues
"""
import time
import logging
from functools import wraps
from sqlalchemy.exc import OperationalError, DisconnectionError
from app.extensions import db


def with_database_retry(max_retries=3, delay=2):
    """
    Decorator to retry database operations with exponential backoff
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (OperationalError, DisconnectionError) as e:
                    last_exception = e
                    
                    if attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt)  # Exponential backoff
                        logging.warning(f"Database connection failed (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s: {str(e)}")
                        time.sleep(wait_time)
                        
                        # Try to reconnect
                        try:
                            db.session.remove()
                            db.engine.dispose()
                        except Exception:
                            pass
                    else:
                        logging.error(f"Database connection failed after {max_retries} attempts: {str(e)}")
            
            raise last_exception
        return wrapper
    return decorator


def test_database_connection():
    """
    Test database connection with retry logic
    """
    max_retries = 5
    delay = 3
    
    for attempt in range(max_retries):
        try:
            from sqlalchemy import text
            result = db.session.execute(text('SELECT 1 as test'))
            result.fetchone()
            
            if attempt > 0:
                logging.info(f"Database connection established after {attempt + 1} attempts")
            else:
                logging.info("Database connection established successfully")
            
            return True
            
        except (OperationalError, DisconnectionError) as e:
            if attempt < max_retries - 1:
                wait_time = delay * (2 ** attempt)
                logging.warning(f"Database test failed (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s: {str(e)}")
                time.sleep(wait_time)
                
                # Try to reconnect
                try:
                    db.session.remove()
                    db.engine.dispose()
                except Exception:
                    pass
            else:
                logging.error(f"Database test failed after {max_retries} attempts: {str(e)}")
                return False
    
    return False


def initialize_database_with_retry():
    """
    Initialize database with connection retry logic
    """
    max_retries = 5
    delay = 3
    
    for attempt in range(max_retries):
        try:
            # Test basic connection first
            if test_database_connection():
                logging.info("Database initialization completed successfully")
                return True
            
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = delay * (2 ** attempt)
                logging.warning(f"Database initialization failed (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s: {str(e)}")
                time.sleep(wait_time)
            else:
                logging.error(f"Database initialization failed after {max_retries} attempts: {str(e)}")
                return False
    
    return False
