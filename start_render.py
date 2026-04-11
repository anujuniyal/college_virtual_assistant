#!/usr/bin/env python3
"""
Render startup script that sets environment variables and starts the application
"""
import os
import sys

def set_render_environment():
    """Set environment variables for Render deployment"""
    
    # Neon Database Configuration
    os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_vVJ1xS3CwXIf@ep-small-tree-anl3swp3-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
    os.environ['POSTGRESQL_URL'] = 'postgresql://neondb_owner:npg_vVJ1xS3CwXIf@ep-small-tree-anl3swp3-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
    os.environ['NEON_DATABASE_URL'] = 'postgresql://neondb_owner:npg_vVJ1xS3CwXIf@ep-small-tree-anl3swp3-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
    
    # Flask Configuration
    os.environ['FLASK_ENV'] = 'production'
    
    # Admin credentials
    os.environ['DEFAULT_ADMIN_USERNAME'] = 'admin'
    os.environ['DEFAULT_ADMIN_EMAIL'] = 'admin@edubot.com'
    os.environ['DEFAULT_ADMIN_PASSWORD'] = 'admin123'
    os.environ['DEFAULT_ADMIN_ROLE'] = 'admin'
    os.environ['ADMIN_EMAIL'] = 'admin@edubot.com'
    
    print("Environment variables set for Render deployment")
    print(f"DATABASE_URL: {os.environ.get('DATABASE_URL', 'NOT_SET')[:50]}...")
    print(f"FLASK_ENV: {os.environ.get('FLASK_ENV', 'NOT_SET')}")

def start_application():
    """Start the Gunicorn application"""
    import subprocess
    
    # Get the port from Render or use default
    port = os.environ.get('PORT', '5000')
    
    # Gunicorn command
    cmd = [
        'gunicorn',
        '--bind', f'0.0.0.0:{port}',
        '--workers', '1',
        '--threads', '2',
        '--timeout', '120',
        '--max-requests', '1000',
        '--max-requests-jitter', '100',
        '--limit-request-line', '4094',
        '--limit-request-field-size', '8190',
        '--preload',
        '--worker-class', 'sync',
        'wsgi:app'
    ]
    
    print(f"Starting application on port {port}")
    subprocess.run(cmd)

if __name__ == '__main__':
    set_render_environment()
    start_application()
