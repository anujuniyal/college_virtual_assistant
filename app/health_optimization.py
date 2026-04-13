"""
Health Check Optimization for Render Deployment
"""
import os
import time
from datetime import datetime

def optimized_health_check():
    """
    Optimized health check with timeout protection
    """
    try:
        from app.offline_mode import OfflineMode
        
        # Check if we're in offline mode first (fastest check)
        if OfflineMode.is_enabled():
            return {
                'status': 'healthy',
                'mode': 'offline',
                'database': 'offline_mode',
                'timestamp': datetime.utcnow().isoformat(),
                'response_time': '<1ms'
            }
        
        # Quick database connectivity test with timeout
        start_time = time.time()
        try:
            from app.offline_mode import offline_database_test
            
            # Use the existing offline_database_test with timeout
            if offline_database_test():
                response_time = round((time.time() - start_time) * 1000, 2)
                return {
                    'status': 'healthy',
                    'mode': 'online',
                    'database': 'connected',
                    'timestamp': datetime.utcnow().isoformat(),
                    'response_time': f'{response_time}ms'
                }
            else:
                return {
                    'status': 'unhealthy',
                    'mode': 'online',
                    'database': 'disconnected',
                    'timestamp': datetime.utcnow().isoformat(),
                    'response_time': f'{round((time.time() - start_time) * 1000, 2)}ms'
                }
                
        except Exception as db_error:
            response_time = round((time.time() - start_time) * 1000, 2)
            return {
                'status': 'unhealthy',
                'mode': 'online',
                'database': 'error',
                'error': str(db_error),
                'timestamp': datetime.utcnow().isoformat(),
                'response_time': f'{response_time}ms'
            }
            
    except Exception as e:
        return {
            'status': 'error',
            'mode': 'unknown',
            'database': 'unknown',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat(),
            'response_time': 'N/A'
        }

def get_worker_info():
    """
    Get worker information for debugging
    """
    return {
        'worker_id': os.environ.get('GUNICORN_WORKER_ID', 'master'),
        'platform': 'Render' if os.environ.get('RENDER') == 'true' else 'Unknown',
        'service_id': os.environ.get('RENDER_SERVICE_ID', 'N/A'),
        'service_name': os.environ.get('RENDER_SERVICE_NAME', 'N/A'),
        'timestamp': datetime.utcnow().isoformat()
    }
