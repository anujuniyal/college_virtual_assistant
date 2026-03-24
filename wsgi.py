"""
WSGI Entry Point for Production
"""
import os
import sys
from dotenv import load_dotenv
from app import create_app

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Load environment variables from .env file
load_dotenv()

# Set production environment
os.environ['FLASK_ENV'] = 'production'

# Get configuration from environment
config_name = os.environ.get('FLASK_ENV', 'production')

# Create app with production configuration
app = create_app(config_name)

# Handle errors gracefully
@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors gracefully"""
    import traceback
    error_details = traceback.format_exc()
    app.logger.error(f"500 Error: {error_details}")
    
    # Return a user-friendly error page
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Server Error</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0; 
                padding: 50px; 
                display: flex; 
                justify-content: center; 
                align-items: center; 
                min-height: 100vh;
            }
            .error-card { 
                background: white; 
                padding: 40px; 
                border-radius: 10px; 
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                text-align: center;
                max-width: 500px;
            }
            h1 { color: #e74c3c; margin-bottom: 20px; }
            p { color: #555; line-height: 1.6; margin-bottom: 30px; }
            .btn { 
                background: #3498db; 
                color: white; 
                padding: 12px 30px; 
                text-decoration: none; 
                border-radius: 5px; 
                display: inline-block;
                transition: background 0.3s;
            }
            .btn:hover { background: #2980b9; }
        </style>
    </head>
    <body>
        <div class="error-card">
            <h1>Oops! Something went wrong</h1>
            <p>We're experiencing a technical issue. Our team has been notified and is working to fix this.</p>
            <a href="/auth/login" class="btn">Go to Login</a>
        </div>
    </body>
    </html>
    """, 500

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Page Not Found</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0; 
                padding: 50px; 
                display: flex; 
                justify-content: center; 
                align-items: center; 
                min-height: 100vh;
            }
            .error-card { 
                background: white; 
                padding: 40px; 
                border-radius: 10px; 
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                text-align: center;
                max-width: 500px;
            }
            h1 { color: #f39c12; margin-bottom: 20px; }
            p { color: #555; line-height: 1.6; margin-bottom: 30px; }
            .btn { 
                background: #3498db; 
                color: white; 
                padding: 12px 30px; 
                text-decoration: none; 
                border-radius: 5px; 
                display: inline-block;
                transition: background 0.3s;
            }
            .btn:hover { background: #2980b9; }
        </style>
    </head>
    <body>
        <div class="error-card">
            <h1>Page Not Found</h1>
            <p>The page you're looking for doesn't exist.</p>
            <a href="/auth/login" class="btn">Go to Login</a>
        </div>
    </body>
    </html>
    """, 404

if __name__ == '__main__':
    # Development server only
    debug_mode = config_name == 'development'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
