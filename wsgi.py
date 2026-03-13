"""
WSGI Entry Point for Production
"""
import os
from dotenv import load_dotenv
from app import create_app

# Load environment variables from .env file
load_dotenv()

# Get configuration from environment
config_name = os.environ.get('FLASK_ENV', 'production')

# Create app with production configuration
app = create_app(config_name)

if __name__ == '__main__':
    # Development server only
    debug_mode = config_name == 'development'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
