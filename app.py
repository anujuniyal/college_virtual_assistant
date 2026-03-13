from app.factory import create_app

def create_app():
    """Create Flask application using factory pattern"""
    from app.factory import create_app as factory_create_app
    return factory_create_app()

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
