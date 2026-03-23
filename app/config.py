"""
Application Configuration
"""
import os
from datetime import timedelta

# Load environment variables from .env file BEFORE any configuration
try:
    from dotenv import load_dotenv
    # Get the project root directory (app/config.py -> project root)
    project_root = os.path.dirname(os.path.dirname(__file__))
    dotenv_path = os.path.join(project_root, '.env')
    load_dotenv(dotenv_path)
except ImportError:
    # If python-dotenv is not available, continue without it
    pass


class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    
    # Database configuration with automatic switching
    @staticmethod
    def _get_database_uri():
        """Determine database URI based on environment"""
        # Check if explicitly set DATABASE_URL (Render provides this)
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            # Handle Render PostgreSQL URLs
            if database_url.startswith('postgres://'):
                # Convert postgres:// to postgresql:// for SQLAlchemy compatibility
                database_url = database_url.replace('postgres://', 'postgresql://', 1)
            return database_url
        
        # Check if we're in production environment
        if os.environ.get('FLASK_ENV') == 'production':
            # In production, default to PostgreSQL if no DATABASE_URL is set
            postgres_url = os.environ.get('POSTGRESQL_URL')
            if postgres_url:
                return postgres_url
            # Fallback to SQLite for local production testing
            pass
        
        # Default to SQLite for local development (use instance folder for Flask best practice)
        return 'sqlite:///instance/edubot_management.db'
    
    # Set the database URI using a function call
    SQLALCHEMY_DATABASE_URI = _get_database_uri()
    
    # Default Admin Credentials (from environment)
    DEFAULT_ADMIN_USERNAME = os.environ.get('DEFAULT_ADMIN_USERNAME') or 'admin'
    DEFAULT_ADMIN_EMAIL = os.environ.get('DEFAULT_ADMIN_EMAIL') or 'admin@edubot.com'
    DEFAULT_ADMIN_PASSWORD = os.environ.get('DEFAULT_ADMIN_PASSWORD') or 'admin123'
    DEFAULT_ADMIN_ROLE = os.environ.get('DEFAULT_ADMIN_ROLE') or 'admin'
    
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN') or ''
    
    # Twilio WhatsApp Configuration
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID') or ''
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN') or ''
    TWILIO_WHATSAPP_FROM = os.environ.get('TWILIO_WHATSAPP_FROM') or 'whatsapp:+14155238886'
    
    # Email Configuration (for OTP)
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or ''
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or ''
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@edubot.management'
    
    # Admin Email for Weekly Reports
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@edubot.management'
    
    # OTP Configuration
    OTP_EXPIRY_MINUTES = int(os.environ.get('OTP_EXPIRY_MINUTES') or 10)
    
    # Rate Limiting
    RATE_LIMIT_RESULT_QUERIES = int(os.environ.get('RATE_LIMIT_RESULT_QUERIES') or 1)  # per day
    RATE_LIMIT_FEE_QUERIES = int(os.environ.get('RATE_LIMIT_FEE_QUERIES') or 1)  # per day
    
    # Notification Expiry
    # Notices should expire quickly for memory efficiency (3–4 days).
    NOTIFICATION_EXPIRY_DAYS = int(os.environ.get('NOTIFICATION_EXPIRY_DAYS') or 4)
    
    # Result Visibility
    RESULT_VISIBILITY_DAYS = int(os.environ.get('RESULT_VISIBILITY_DAYS') or 7)
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    
    # File Upload Configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Security settings
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() in ['true', 'on', '1']
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    @classmethod
    def init_app(cls, app):
        """Initialize app with base configuration"""
        pass


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Ensure PostgreSQL is used in production
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Force database URI check for production
        if not os.environ.get('DATABASE_URL'):
            app.logger.warning("No DATABASE_URL found in production - authentication may fail")
        
        # Production logging
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug and not app.testing:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            
            file_handler = RotatingFileHandler('logs/edubot.log', maxBytes=10240000, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            
            app.logger.setLevel(logging.INFO)
            app.logger.info('EduBot Production Startup')
    
    # Security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # Logging
    LOG_LEVEL = 'INFO'
    
    # Rate limiting (more restrictive in production)
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')
    
    # File upload restrictions
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8MB in production


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    
    # Less restrictive for development
    SESSION_COOKIE_SECURE = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB in development


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    
    # Use in-memory database for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
