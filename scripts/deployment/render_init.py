#!/usr/bin/env python3
"""
Render Deployment Initialization Script
This script properly initializes the database for Render deployment
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set production environment
os.environ['FLASK_ENV'] = 'production'

def init_render_deployment():
    """Initialize database for Render deployment"""
    try:
        print("🚀 Initializing Render deployment...")
        
        # Import and run the main initialization
        from scripts.deployment.init_production_db import init_production_database
        success = init_production_database()
        
        if success:
            print("✅ Render deployment initialized successfully!")
            print("\n📋 Login Credentials:")
            print("Email: admin@edubot.com")
            print("Password: admin123")
            print("\n⚠️  Change password after first login!")
            return True
        else:
            print("❌ Render deployment initialization failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error during Render initialization: {str(e)}")
        return False

if __name__ == '__main__':
    success = init_render_deployment()
    sys.exit(0 if success else 1)
