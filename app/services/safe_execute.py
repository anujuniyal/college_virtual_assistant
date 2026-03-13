"""
Safe execution utility for database operations
"""
import logging

logger = logging.getLogger(__name__)

def safe_execute(func, default=None):
    """
    Safely execute a function and return result or default value
    
    Args:
        func: Function to execute
        default: Default value to return if function fails
    
    Returns:
        Function result or default value
    """
    try:
        result = func()
        return result
    except Exception as e:
        logger.error(f"Safe execute error: {str(e)}")
        return default

def safe_execute_with_logging(func, operation_name="database operation"):
    """
    Safely execute a function with detailed logging
    
    Args:
        func: Function to execute
        operation_name: Description of operation for logging
    
    Returns:
        Function result or None
    """
    try:
        result = func()
        logger.info(f"Successfully executed {operation_name}")
        return result
    except Exception as e:
        logger.error(f"Error in {operation_name}: {str(e)}")
        return None

def safe_database_query(query_func, default=None):
    """
    Safely execute a database query
    
    Args:
        query_func: Database query function
        default: Default value to return if query fails
    
    Returns:
        Query result or default value
    """
    try:
        result = query_func()
        return result
    except Exception as e:
        logger.error(f"Database query error: {str(e)}")
        return default
