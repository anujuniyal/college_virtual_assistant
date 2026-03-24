"""
Simple health check that doesn't require database connection
"""
import os
import sys
from flask import jsonify, Flask

def create_simple_health_app():
    """Create a minimal Flask app for health checks"""
    app = Flask(__name__)
    
    @app.route('/health')
    def health():
        """Simple health check without database dependency"""
        return jsonify({
            'status': 'healthy',
            'database': 'checking',
            'timestamp': '2026-03-24T11:00:00.000Z',
            'message': 'Application is running'
        })
    
    @app.route('/')
    def index():
        """Root endpoint"""
        return jsonify({
            'status': 'running',
            'service': 'college-virtual-assistant',
            'message': 'Application is running'
        })
    
    return app

if __name__ == '__main__':
    app = create_simple_health_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
