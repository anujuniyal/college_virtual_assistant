"""
Optimized Startup Module to Prevent Worker Timeouts
"""
import os
import threading
import time
from datetime import datetime

def initialize_services_async(app):
    """
    Initialize services asynchronously to prevent worker timeouts
    """
    def async_init():
        try:
            # Small delay to let the worker start properly
            time.sleep(1)
            
            # Check if running on Render to skip cleanup during startup
            is_render = (
                os.environ.get('RENDER') == 'true' or 
                os.environ.get('RENDER_SERVICE_ID') is not None
            )
            
            if not is_render:
                # Initialize cleanup service with error handling (only for local/production non-Render)
                from app.services.cleanup_service import CleanupService
                
                cleanup_service = CleanupService()
                
                # Run cleanup with timeout protection
                try:
                    notifications_result = cleanup_service.cleanup_expired_notifications()
                    results_result = cleanup_service.cleanup_expired_results()
                    otps_result = cleanup_service.cleanup_expired_otps()
                    
                    result = {
                        'notifications': notifications_result,
                        'results': results_result,
                        'otps': otps_result
                    }
                    app.logger.info(f"Async cleanup completed: {result}")
                except Exception as cleanup_error:
                    app.logger.warning(f"Async cleanup service failed (non-critical): {str(cleanup_error)}")
            else:
                # Skip cleanup on Render to prevent worker timeouts
                app.logger.info("Skipping cleanup service on Render for faster startup")
            
            # Log worker information for debugging
            worker_id = os.environ.get('GUNICORN_WORKER_ID', 'master')
            app.logger.info(f"🔄 Async worker {worker_id} initialization completed")
            
        except Exception as e:
            app.logger.error(f"Error in async service initialization: {str(e)}")
    
    # Start initialization in background thread
    init_thread = threading.Thread(target=async_init, daemon=True)
    init_thread.start()
    
    return True

def safe_subprocess_call(command, timeout=30):
    """
    Safely execute subprocess with timeout to prevent blocking
    """
    import subprocess
    
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            return {
                'success': process.returncode == 0,
                'stdout': stdout,
                'stderr': stderr,
                'returncode': process.returncode
            }
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            return {
                'success': False,
                'error': f'Command timed out after {timeout} seconds',
                'stdout': '',
                'stderr': 'Process killed due to timeout'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'stdout': '',
            'stderr': ''
        }

def safe_psutil_operation(operation_func, timeout=10):
    """
    Safely execute psutil operations with timeout
    """
    def timeout_wrapper():
        try:
            return operation_func()
        except Exception as e:
            return {'error': str(e)}
    
    # Use threading to implement timeout
    result_container = {'result': None, 'done': False}
    
    def target():
        result_container['result'] = timeout_wrapper()
        result_container['done'] = True
    
    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout)
    
    if not result_container['done']:
        return {'error': f'Operation timed out after {timeout} seconds'}
    
    return result_container['result']
