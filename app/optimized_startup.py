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
    # DISABLED: Skip async initialization completely to prevent worker issues on Render
    worker_id = os.environ.get('GUNICORN_WORKER_ID', 'master')
    
    if worker_id != 'master':
        app.logger.info(f"Skipping async initialization for worker {worker_id}")
        return True
    
    # Only run basic cleanup on Render to prevent timeouts
    is_render = (
        os.environ.get('RENDER') == 'true' or 
        os.environ.get('RENDER_SERVICE_ID') is not None
    )
    
    if is_render:
        app.logger.info("Skipping all async services on Render for maximum stability")
        return True
    
    # For local development only
    try:
        from app.services.optimized_otp_service import OptimizedOTPService
        OptimizedOTPService.cleanup_cache()
        app.logger.info("OTP cache cleanup completed")
    except Exception as e:
        app.logger.warning(f"OTP cache cleanup failed: {str(e)}")
    
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
