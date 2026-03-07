"""
Flask Application Factory Pattern Implementation
"""

import os
from flask import Flask
from app.config import config
from app.extensions import db, login_manager, mail


def create_app(config_name=None):
    """
    Application Factory Pattern
    
    Creates and configures Flask application with proper separation of concerns
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    # Create Flask application instance
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions
    initialize_extensions(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register CLI commands
    register_cli_commands(app)
    
    # Initialize application context
    with app.app_context():
        initialize_database(app)
        initialize_services(app)
    
    return app


def initialize_extensions(app):
    """Initialize Flask extensions"""
    # Database
    db.init_app(app)
    
    # Authentication
    login_manager.init_app(app)
    
    # Email
    mail.init_app(app)
    
    # Setup user loader
    @login_manager.user_loader
    def load_user(user_id):
        """Load user for Flask-Login"""
        try:
            from app.models import Admin
            return Admin.query.get(int(user_id))
        except Exception as e:
            app.logger.error(f"Error loading user: {str(e)}")
            return None


def register_blueprints(app):
    """Register application blueprints"""
    # Import and register blueprints
    from app.blueprints import admin, auth, faculty, accounts, telegram
    
    # Register auth first
    app.register_blueprint(auth.auth_bp)
    
    # Register other blueprints
    app.register_blueprint(admin.admin_bp)
    app.register_blueprint(faculty.faculty_bp)
    app.register_blueprint(accounts.accounts_bp)
    app.register_blueprint(telegram.telegram_bp)


def register_error_handlers(app):
    """Register error handlers"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors"""
        from flask import render_template, jsonify, request
        
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Resource not found'}), 404
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        from flask import render_template, jsonify, request
        
        db.session.rollback()
        
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 errors"""
        from flask import render_template, jsonify, request
        
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Access forbidden'}), 403
        return render_template('errors/403.html'), 403


def register_cli_commands(app):
    """Register CLI commands"""
    
    @app.cli.command()
    def init_db():
        """Initialize database"""
        from app.models import Admin, Student, Faculty, Notification, Result, FeeRecord, Complaint, ChatbotQA, ChatbotUnknown
        
        db.create_all()
        print("✅ Database tables created successfully!")
    
    @app.cli.command()
    def create_admin():
        """Create default admin user"""
        from app.models import Admin
        from werkzeug.security import generate_password_hash
        
        admin = Admin.query.filter_by(username='admin').first()
        if not admin:
            admin = Admin(
                username='admin',
                email='admin@edubot.com',
                password_hash=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Default admin user created!")
        else:
            print("ℹ️ Admin user already exists!")
    
    @app.cli.command()
    def cleanup_data():
        """Clean up old data"""
        from app.services.cleanup_service import CleanupService
        
        cleanup_service = CleanupService()
        result = cleanup_service.cleanup_old_data()
        print(f"✅ Cleanup completed: {result}")


def initialize_database(app):
    """Initialize database tables and default data"""
    try:
        # Create all tables
        db.create_all()
        app.logger.info("Database tables created successfully")
        
        # Create default admin if not exists
        from app.models import Admin
        from werkzeug.security import generate_password_hash
        
        admin = Admin.query.filter_by(username='admin').first()
        if not admin:
            # Also check if email already exists
            existing_email = Admin.query.filter_by(email='admin@edubot.com').first()
            if not existing_email:
                admin = Admin(
                    username='admin',
                    email='admin@edubot.com',
                    password_hash=generate_password_hash('admin123'),
                    role='admin'
                )
                db.session.add(admin)
                db.session.commit()
                app.logger.info("Default admin user created")
            else:
                app.logger.info("Admin email already exists, skipping admin creation")
        else:
            app.logger.info("Admin user already exists, skipping admin creation")
        
    except Exception as e:
        app.logger.error(f"Error initializing database: {str(e)}")
        # Don't raise exception to allow app to continue
        pass


def initialize_services(app):
    """Initialize application services"""
    try:
        # Initialize cleanup service
        from app.services.cleanup_service import CleanupService
        
        cleanup_service = CleanupService()
        # Use the correct method name
        notifications_result = cleanup_service.cleanup_expired_notifications()
        results_result = cleanup_service.cleanup_expired_results()
        otps_result = cleanup_service.cleanup_expired_otps()
        
        result = {
            'notifications': notifications_result,
            'results': results_result,
            'otps': otps_result
        }
        app.logger.info(f"Cleanup on startup: {result}")
        
    except Exception as e:
        app.logger.error(f"Error initializing services: {str(e)}")


def configure_logging(app):
    """Configure application logging"""
    import logging
    from logging.handlers import RotatingFileHandler
    
    if not app.debug and not app.testing:
        # Create logs directory if not exists
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Configure file handler
        file_handler = RotatingFileHandler(
            'logs/edubot.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('EduBot Production Startup')
