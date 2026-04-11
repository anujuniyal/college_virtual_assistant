#!/usr/bin/env python3
"""
Debug script to check environment variables on Render
"""

import os
import sys

def print_env_debug():
    """Print all environment variables for debugging"""
    print("=== RENDER ENVIRONMENT DEBUG ===")
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    
    # Check for Render-specific environment
    print(f"\nRENDER environment: {os.environ.get('RENDER', 'NOT_SET')}")
    print(f"RENDER_SERVICE_ID: {os.environ.get('RENDER_SERVICE_ID', 'NOT_SET')}")
    print(f"RENDER_SERVICE_NAME: {os.environ.get('RENDER_SERVICE_NAME', 'NOT_SET')}")
    print(f"PORT: {os.environ.get('PORT', 'NOT_SET')}")
    
    # Database configuration
    print(f"\nDATABASE_URL: {os.environ.get('DATABASE_URL', 'NOT_SET')}")
    print(f"POSTGRESQL_URL: {os.environ.get('POSTGRESQL_URL', 'NOT_SET')}")
    print(f"NEON_DATABASE_URL: {os.environ.get('NEON_DATABASE_URL', 'NOT_SET')}")
    
    # Flask configuration
    print(f"\nFLASK_ENV: {os.environ.get('FLASK_ENV', 'NOT_SET')}")
    print(f"SECRET_KEY: {'SET' if os.environ.get('SECRET_KEY') else 'NOT_SET'}")
    
    # Admin configuration
    print(f"\nDEFAULT_ADMIN_USERNAME: {os.environ.get('DEFAULT_ADMIN_USERNAME', 'NOT_SET')}")
    print(f"DEFAULT_ADMIN_EMAIL: {os.environ.get('DEFAULT_ADMIN_EMAIL', 'NOT_SET')}")
    print(f"DEFAULT_ADMIN_PASSWORD: {'SET' if os.environ.get('DEFAULT_ADMIN_PASSWORD') else 'NOT_SET'}")
    
    print("\n=== ALL ENVIRONMENT VARIABLES ===")
    for key, value in sorted(os.environ.items()):
        if 'PASSWORD' in key or 'SECRET' in key or 'TOKEN' in key:
            print(f"{key}: [REDACTED]")
        else:
            print(f"{key}: {value}")

if __name__ == '__main__':
    print_env_debug()
