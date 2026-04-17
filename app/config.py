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

    

    # Load base .env file first (local development)

    dotenv_path = os.path.join(project_root, '.env')

    if os.path.exists(dotenv_path):

        load_dotenv(dotenv_path)

    

    # Check if running on Render (multiple detection methods)

    is_render_deployment = (

        os.environ.get('RENDER') == 'true' or 

        os.environ.get('RENDER_SERVICE_ID') is not None or

        os.environ.get('RENDER_SERVICE_NAME') is not None or

        os.path.exists('/etc/render') or

        'render.com' in os.environ.get('HOME', '')

    )

    

    # Debug environment detection

    print("🔍 Environment Detection:")

    print(f"   RENDER: {os.environ.get('RENDER', 'NOT_SET')}")

    print(f"   RENDER_SERVICE_ID: {os.environ.get('RENDER_SERVICE_ID', 'NOT_SET')}")

    print(f"   RENDER_SERVICE_NAME: {os.environ.get('RENDER_SERVICE_NAME', 'NOT_SET')}")

    print(f"   HOME: {os.environ.get('HOME', 'NOT_SET')}")

    print(f"   /etc/render exists: {os.path.exists('/etc/render')}")

    print(f"   Is Render: {is_render_deployment}")

    

    # Load .env.render ONLY for local development/testing, NOT on Render

    if not is_render_deployment:

        dotenv_render_path = os.path.join(project_root, '.env.render')

        if os.path.exists(dotenv_render_path):

            load_dotenv(dotenv_render_path, override=True)

            print(f"Loaded render config from {dotenv_render_path}")

    else:

        print("🚀 Running on Render - using environment variables from render.yaml")

    

    # Load production-specific .env file if in production (local only)

    if os.environ.get('FLASK_ENV') == 'production' and not is_render_deployment:

        dotenv_prod_path = os.path.join(project_root, '.env.production')

        if os.path.exists(dotenv_prod_path):

            load_dotenv(dotenv_prod_path, override=False)

            print(f"Loaded production config from {dotenv_prod_path}")

        else:

            print("Warning: .env.production file not found")

            

except ImportError:

    # If python-dotenv is not available, continue without it

    pass





class Config:

    """Base configuration"""

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')

    SERVER_NAME = os.environ.get('SERVER_NAME', None)

    PREFERRED_URL_SCHEME = 'https' if os.environ.get('RENDER') else 'http'

    APPLICATION_ROOT = '/'

    SQLALCHEMY_TRACK_MODIFICATIONS = True

    SQLALCHEMY_DATABASE_URI = None  # Will be set dynamically

    

    # SQLAlchemy engine optimizations for Neon

    SQLALCHEMY_ENGINE_OPTIONS = {

        'pool_pre_ping': True,  # Check connections before use

        'pool_recycle': 300,     # Recycle connections every 5 minutes

        'echo': False           # Set to True for SQL debugging

    }

    

    # Default Admin Credentials (from environment)

    DEFAULT_ADMIN_USERNAME = os.environ.get('DEFAULT_ADMIN_USERNAME') or 'admin'

    DEFAULT_ADMIN_EMAIL = os.environ.get('DEFAULT_ADMIN_EMAIL') or 'admin@edubot.com'

    DEFAULT_ADMIN_PASSWORD = os.environ.get('DEFAULT_ADMIN_PASSWORD') or 'admin123'

    DEFAULT_ADMIN_ROLE = os.environ.get('DEFAULT_ADMIN_ROLE') or 'admin'

    

    # Real-time updates configuration for Neon

    SQLALCHEMY_RECORD_QUERIES = False  # Disable query recording for better performance

    SQLALCHEMY_COMMIT_ON_TEARDOWN = True  # Ensure auto-commit for real-time updates

    

    # Telegram Bot Configuration

    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN') or ''
    
    # Public Base URL for Telegram Webhooks (HTTPS required)
    PUBLIC_BASE_URL = os.environ.get('PUBLIC_BASE_URL', 'https://localhost:5000')

    

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

        # Set database URI dynamically based on environment

        database_uri = cls._get_database_uri()

        app.config['SQLALCHEMY_DATABASE_URI'] = database_uri

        

        # Debug: Print all environment variables

        is_render = os.environ.get('RENDER') == 'true' or os.path.exists('/etc/render')

        print("🔍 DEBUG: Environment variables:")

        print(f"   Platform: {'Render' if is_render else 'Local'}")

        print(f"   FLASK_ENV: {os.environ.get('FLASK_ENV', 'NOT_SET')}")

        print(f"   DATABASE_URL: {os.environ.get('DATABASE_URL', 'NOT_SET')}")

        print(f"   POSTGRESQL_URL: {os.environ.get('POSTGRESQL_URL', 'NOT_SET')}")

        print(f"   Final Database URI: {database_uri}")

        

        # Warn if no database URL in production

        if os.environ.get('FLASK_ENV') == 'production' and not os.environ.get('DATABASE_URL'):

            app.logger.warning("⚠️  No DATABASE_URL found - check render.yaml configuration!")

    

    @staticmethod

    def _get_database_uri():

        """Determine database URI based on environment"""

        # Prioritize Neon database for local development

        neon_url = os.environ.get('NEON_DATABASE_URL')

        if neon_url and neon_url != 'your_neon_connection_string_here':

            print(f"✅ Using NEON_DATABASE_URL: {neon_url[:50]}...")

            return neon_url

        

        # Check if explicitly set DATABASE_URL (Render provides this)

        database_url = os.environ.get('DATABASE_URL')

        

        print("🔍 Database Configuration Debug:")

        print(f"   DATABASE_URL: {database_url[:50] + '...' if database_url and len(database_url) > 50 else database_url}")

        print(f"   POSTGRESQL_URL: {os.environ.get('POSTGRESQL_URL', 'NOT_SET')}")

        print(f"   FLASK_ENV: {os.environ.get('FLASK_ENV', 'NOT_SET')}")

        

        # Handle DATABASE_URL if available

        if database_url:

            # Handle Render PostgreSQL URLs

            if database_url.startswith('postgres://'):

                # Convert postgres:// to postgresql:// for SQLAlchemy compatibility

                database_url = database_url.replace('postgres://', 'postgresql://', 1)

            

            # Add Neon-specific optimizations for production

            if os.environ.get('FLASK_ENV') == 'production':

                # Add connection pooling parameters for better performance

                if '?' not in database_url:

                    database_url += '?'

                else:

                    database_url += '&'

                

                # Neon/PostgreSQL optimization parameters for network resilience

                database_url += 'sslmode=disable&connect_timeout=30&application_name=edubot_render&keepalives=1&keepalives_idle=30&keepalives_interval=10&keepalives_count=5'

            

            print(f"✅ Using DATABASE_URL (Neon): {database_url[:50]}...")

            return database_url

        

        # Check if we're in production environment

        if os.environ.get('FLASK_ENV') == 'production':

            # In production, check for POSTGRESQL_URL

            postgres_url = os.environ.get('POSTGRESQL_URL')

            

            if postgres_url:

                if postgres_url.startswith('postgres://'):

                    postgres_url = postgres_url.replace('postgres://', 'postgresql://', 1)

                print(f"✅ Using POSTGRESQL_URL: {postgres_url[:50]}...")

                return postgres_url

            

            # CRITICAL: In production, we MUST have a database URL
            print("❌ PRODUCTION ERROR: No DATABASE_URL or POSTGRESQL_URL found!")
            print("❌ Application cannot start without PostgreSQL database")
            
            # Fail fast - no SQLite fallback for production
            raise RuntimeError("Production deployment requires DATABASE_URL or POSTGRESQL_URL environment variable")

        

        # Default to PostgreSQL for local development
        print("❌ DEVELOPMENT ERROR: No database URL configured")
        print("❌ Please set NEON_DATABASE_URL or DATABASE_URL environment variable")
        
        # Fail fast - no SQLite fallback
        raise RuntimeError("Development requires NEON_DATABASE_URL or DATABASE_URL environment variable")





class ProductionConfig(Config):

    """Production configuration"""

    DEBUG = False

    TESTING = False

    

    # Optimized database settings for memory efficiency (<400MB)

    SQLALCHEMY_ENGINE_OPTIONS = {

        **Config.SQLALCHEMY_ENGINE_OPTIONS,

        'pool_size': 1,           # Single connection for memory efficiency

        'max_overflow': 1,       # Minimal overflow

        'pool_timeout': 20,       # Shorter timeout

        'pool_recycle': 600,      # Recycle every 10 minutes

        'pool_pre_ping': True,     # Validate connections

        'pool_reset_on_return': 'commit',  # Reset connection state

    }

    

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

            app.logger.info('EduBot Production Startup with Neon')

    

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

    

    # Use PostgreSQL test database for testing

    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or os.environ.get('DATABASE_URL')

    

    # Disable CSRF for testing

    WTF_CSRF_ENABLED = False





# Configuration mapping

config = {

    'development': DevelopmentConfig,

    'testing': TestingConfig,

    'production': ProductionConfig,

    'default': DevelopmentConfig

}
