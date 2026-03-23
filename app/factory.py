"""
Flask Application Factory Pattern Implementation
"""

import os
from functools import wraps
from flask import Flask, current_app
from flask_login import current_user
from app.config import config
from app.extensions import db, login_manager, mail

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Get the project root directory (app/factory.py -> project root)
    project_root = os.path.dirname(os.path.dirname(__file__))
    dotenv_path = os.path.join(project_root, '.env')
    load_dotenv(dotenv_path)
except ImportError:
    # If python-dotenv is not available, continue without it
    pass


def create_app(config_name=None):
    """
    Application Factory Pattern
    
    Creates and configures Flask application with proper separation of concerns
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    # Get the absolute path to the app directories
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    
    # Create Flask application instance with correct template and static folders
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    
    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions
    initialize_extensions(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register application routes
    from app.routes import register_routes
    register_routes(app)

    # Register small core routes
    register_core_routes(app)
    
    # Register template context processors
    register_context_processors(app)
    
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


def register_blueprints(app):
    """Register application blueprints"""
    # Import and register blueprints
    from app.blueprints import admin, auth, faculty, accounts, telegram, notification
    
    # Register auth first
    app.register_blueprint(auth.auth_bp)
    
    # Register other blueprints
    app.register_blueprint(admin.admin_bp)
    app.register_blueprint(faculty.faculty_bp)
    app.register_blueprint(accounts.accounts_bp)
    app.register_blueprint(telegram.telegram_bp)
    app.register_blueprint(notification.notification_bp)


def register_context_processors(app):
    """Register template context processors"""
    @app.context_processor
    def utility_processor():
        def get_user_role():
            """Get current user's role"""
            if not current_user.is_authenticated:
                return 'student'
            
            # Handle both Admin and Faculty models
            if hasattr(current_user, 'role'):
                return current_user.role
            elif hasattr(current_user, 'user_role'):
                return current_user.user_role
            else:
                return 'student'
        
        def has_write_access():
            """Check if current user has write access to accounts"""
            user_role = get_user_role()
            return user_role == 'accounts'
        
        def is_accounts_role():
            """Check if current user has accounts role"""
            user_role = get_user_role()
            return user_role == 'accounts'
        
        def is_admin_role():
            """Check if current user has admin role"""
            user_role = get_user_role()
            return user_role == 'admin'
        
        def is_faculty_role():
            """Check if current user has faculty role"""
            user_role = get_user_role()
            return user_role == 'faculty'
        
        return {
            'get_user_role': get_user_role,
            'has_write_access': has_write_access,
            'is_accounts_role': is_accounts_role,
            'is_admin_role': is_admin_role,
            'is_faculty_role': is_faculty_role
        }


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


def register_core_routes(app):
    """Register minimal core routes not belonging to a blueprint."""
    from flask import redirect, url_for, request, jsonify
    from datetime import datetime
    from flask_login import login_required, current_user

    def admin_required(f):
        """Decorator to require admin privileges"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Check if user has admin role (supports both Admin and Faculty tables)
            user_role = getattr(current_user, 'role', None) or getattr(current_user, 'user_role', None)
            if user_role != 'admin':
                return jsonify({'error': 'Admin privileges required'}), 403
            
            return f(*args, **kwargs)
        return decorated_function

    def _is_bot_process(proc):
        """Safely check if a process is our bot process"""
        try:
            if not proc.info or not proc.info.get('cmdline'):
                return False
            
            cmdline = ' '.join(proc.info['cmdline'])
            # More specific bot script detection
            bot_scripts = ['simple_telegram_bot.py', 'run_telegram_bot.py', 'activate_telegram_bot.py']
            
            # Check if it's a Python process running our bot script
            is_python = proc.info.get('name') in ['python', 'python.exe']
            is_bot_script = any(script in cmdline for script in bot_scripts)
            
            return is_python and is_bot_script
            
        except Exception:
            return False

    def _safe_terminate_process(proc):
        """Safely terminate a process with proper validation"""
        try:
            if not proc or not proc.is_running():
                return False, "Process not running"
            
            # Additional safety check - verify it's our bot process
            if not _is_bot_process(proc):
                return False, "Process is not a bot process"
            
            proc.terminate()
            return True, "Process terminated successfully"
            
        except psutil.NoSuchProcess:
            return False, "Process no longer exists"
        except psutil.AccessDenied:
            try:
                os.kill(proc.pid, signal.SIGTERM)
                return True, "Process terminated via SIGTERM"
            except Exception:
                return False, "Access denied to process"
        except Exception as e:
            return False, f"Error terminating process: {str(e)}"

    @app.route('/debug/bot-status')
    @login_required
    @admin_required
    def debug_bot_status():
        """Debug bot status endpoint with proper authentication"""
        try:
            import subprocess
            import psutil
            import time
            from datetime import datetime
            
            # Check if bot process is running
            bot_running = False
            bot_info = {
                'status': 'offline',
                'message': 'Bot is not running',
                'last_check': datetime.utcnow().isoformat(),
                'uptime': None,
                'memory_usage': None,
                'cpu_usage': None
            }
            
            # Check for python processes that might be the bot
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent', 'create_time']):
                try:
                    if _is_bot_process(proc):
                        bot_running = True
                        uptime = time.time() - proc.info['create_time'] if proc.info.get('create_time') else 0
                        
                        bot_info.update({
                            'status': 'online',
                            'message': 'Bot is running',
                            'pid': proc.info['pid'],
                            'cpu_usage': round(proc.info['cpu_percent'], 2),
                            'memory_usage': round(proc.info['memory_percent'], 2),
                            'uptime': round(uptime, 2),
                            'cmdline': ' '.join(proc.info['cmdline'] or [])[:100] + '...' if len(' '.join(proc.info['cmdline'] or [])) > 100 else ' '.join(proc.info['cmdline'] or [])
                        })
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return jsonify(bot_info)
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Error checking bot status: {str(e)}',
                'last_check': datetime.utcnow().isoformat()
            }), 500

    @app.route('/debug/toggle-bot', methods=['POST'])
    @login_required
    @admin_required
    def debug_toggle_bot():
        """Debug toggle bot endpoint with proper authentication and security"""
        try:
            import subprocess
            import os
            import signal
            import psutil
            import threading
            from datetime import datetime
            
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'Invalid request data',
                    'status': 'error'
                }), 400
            
            action = data.get('action', 'activate')
            if action not in ['activate', 'deactivate']:
                return jsonify({
                    'success': False,
                    'message': 'Invalid action specified',
                    'status': 'error'
                }), 400
            
            if action == 'activate':
                # Start the bot with proper validation
                try:
                    # Check if bot is already running
                    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                        if _is_bot_process(proc):
                            return jsonify({
                                'success': False,
                                'message': 'Bot is already running',
                                'status': 'online',
                                'pid': proc.info['pid']
                            })
                    
                    # Find and validate bot script
                    bot_script_path = os.path.join(os.getcwd(), 'simple_telegram_bot.py')
                    
                    if not os.path.exists(bot_script_path):
                        return jsonify({
                            'success': False,
                            'message': 'Bot runner script not found',
                            'status': 'error'
                        }), 404
                    
                    if not os.access(bot_script_path, os.X_OK):
                        # Try to make it executable
                        try:
                            os.chmod(bot_script_path, 0o755)
                        except:
                            pass  # Continue even if chmod fails
                    
                    # Track process for proper cleanup
                    process_tracker = {'process': None}
                    
                    def start_bot():
                        try:
                            env = os.environ.copy()
                            env['PYTHONPATH'] = os.getcwd()
                            process = subprocess.Popen([
                                'python', bot_script_path
                            ], 
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            cwd=os.getcwd(),
                            env=env
                            )
                            process_tracker['process'] = process
                            return process
                        except Exception as e:
                            return None
                    
                    # Start bot in background thread with proper tracking
                    def start_bot_thread():
                        bot_process = start_bot()
                        if bot_process:
                            import time
                            time.sleep(2)  # Give bot time to start
                            # Could add process health check here
                    
                    thread = threading.Thread(target=start_bot_thread, daemon=True)
                    thread.start()
                    
                    return jsonify({
                        'success': True,
                        'message': 'Bot activation initiated. Starting up...',
                        'status': 'starting'
                    })
                        
                except Exception as e:
                    return jsonify({
                        'success': False,
                        'message': f'Failed to start bot: {str(e)}',
                        'status': 'error'
                    }), 500
                    
            elif action == 'deactivate':
                # Stop the bot with proper validation
                try:
                    stopped_processes = []
                    errors = []
                    
                    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                        if _is_bot_process(proc):
                            success, message = _safe_terminate_process(proc)
                            if success:
                                stopped_processes.append(proc.info['pid'])
                            else:
                                errors.append(f"PID {proc.info['pid']}: {message}")
                    
                    if stopped_processes:
                        return jsonify({
                            'success': True,
                            'message': f'Bot stopped successfully. Terminated {len(stopped_processes)} process(es).',
                            'status': 'offline',
                            'stopped_processes': stopped_processes
                        })
                    elif errors:
                        return jsonify({
                            'success': False,
                            'message': 'Failed to stop some bot processes',
                            'status': 'error',
                            'errors': errors
                        }), 500
                    else:
                        return jsonify({
                            'success': False,
                            'message': 'No running bot processes found',
                            'status': 'offline'
                        })
                        
                except Exception as e:
                    return jsonify({
                        'success': False,
                        'message': f'Failed to stop bot: {str(e)}',
                        'status': 'error'
                    }), 500
                
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error toggling bot: {str(e)}',
                'status': 'error',
                'last_check': datetime.utcnow().isoformat()
            }), 500

    @app.route('/favicon.ico')
    def favicon():
        """Handle favicon request"""
        from flask import send_from_directory
        import os
        
        # Try to serve favicon from static folder
        favicon_path = os.path.join(app.static_folder, 'favicon.ico')
        if os.path.exists(favicon_path):
            return send_from_directory(app.static_folder, 'favicon.ico')
        
        # Return empty 204 response if no favicon exists
        return '', 204

    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring"""
        from flask import jsonify
        try:
            # Check database connection
            from app.extensions import db
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'database': 'disconnected',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 500


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
        """Create default admin user from environment variables"""
        from app.services.database_setup import DatabaseSetup
        
        result = DatabaseSetup.create_user_from_config('admin')
        if result['success']:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['message']}")
    
    @app.cli.command()
    def reset_admin_password():
        """Reset admin password from environment variables"""
        from app.services.database_setup import DatabaseSetup
        
        result = DatabaseSetup.reset_admin_password()
        if result['success']:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['message']}")
    
    @app.cli.command()
    def create_user(username=None, email=None, password=None, role='admin'):
        """Create a new user"""
        from app.services.user_service import UserService
        
        if not all([username, email, password]):
            print("❌ Username, email, and password are required")
            print("Usage: flask create-user <username> <email> <password> [role]")
            return
        
        # Validate input
        errors = UserService.validate_user_data(username, email, password, role)
        if errors:
            print("❌ Validation errors:")
            for error in errors:
                print(f"   - {error}")
            return
        
        result = UserService.create_user(username, email, password, role)
        if result['success']:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['message']}")
    
    @app.cli.command()
    def list_users():
        """List all users"""
        from app.services.user_service import UserService
        
        users = UserService.get_all_users()
        if not users:
            print("No users found")
            return
        
        print(f"\n{'ID':<5} {'Username':<15} {'Email':<25} {'Role':<10} {'Active':<8}")
        print("-" * 70)
        for user in users:
            print(f"{user.id:<5} {user.username:<15} {user.email:<25} {user.role:<10} {'Yes' if user.is_active else 'No':<8}")
        print()
    
    @app.cli.command()
    def db_info():
        """Show database information"""
        from app.services.database_setup import DatabaseSetup
        
        result = DatabaseSetup.get_database_info()
        if result['success']:
            info = result['info']
            print("\n📊 Database Information:")
            print(f"Users: {info['users']['total']} total")
            print(f"  - Admin: {info['users']['admin']}")
            print(f"  - Faculty: {info['users']['faculty']}")
            print(f"  - Accounts: {info['users']['accounts']}")
            print(f"  - Active: {info['users']['active']}")
            print(f"Students: {info['students']}")
            print(f"Faculty Records: {info['faculty_records']}")
            print()
        else:
            print(f"❌ {result['message']}")
    
    @app.cli.command()
    def validate_config():
        """Validate environment configuration"""
        from app.services.database_setup import DatabaseSetup
        
        result = DatabaseSetup.validate_configuration()
        if result['success']:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['message']}")
    
    @app.cli.command()
    def setup_faculty():
        """Create specified faculty users with roles and passwords"""
        from app.services.faculty_setup import FacultySetup
        
        print("👥 Creating specified faculty users...")
        result = FacultySetup.create_specified_faculty()
        
        if result['success']:
            print(f"✅ Successfully processed {result['total']} faculty users")
            
            if result['created']:
                print("\n🆕 Created Users:")
                for user in result['created']:
                    print(f"  - {user['name']} ({user['role']}) - {user['email']} - Password: {user['password']}")
            
            if result['updated']:
                print("\n🔄 Updated Users:")
                for user in result['updated']:
                    print(f"  - {user['name']} ({user['role']}) - {user['email']} - Password: {user['password']}")
        else:
            print(f"❌ Error: {result['message']}")
    
    @app.cli.command()
    def list_faculty():
        """List all faculty users with their roles"""
        from app.services.faculty_setup import FacultySetup
        
        faculty_list = FacultySetup.list_all_faculty()
        
        if not faculty_list:
            print("No faculty users found")
            return
        
        print(f"\n{'ID':<5} {'Name':<20} {'Email':<25} {'Role':<10} {'Department':<15}")
        print("-" * 80)
        for faculty in faculty_list:
            print(f"{faculty['id']:<5} {faculty['name']:<20} {faculty['email']:<25} {faculty['role']:<10} {faculty['department']:<15}")
        print()
    
    @app.cli.command()
    def faculty_info():
        """Show faculty information by role"""
        from app.services.faculty_setup import FacultySetup
        
        roles = ['admin', 'accounts', 'faculty']
        
        print("\n👥 Faculty Users by Role:")
        print("=" * 50)
        
        for role in roles:
            faculty_list = FacultySetup.get_faculty_by_role(role)
            print(f"\n{role.title()} ({len(faculty_list)}):")
            for faculty in faculty_list:
                print(f"  - {faculty.name} ({faculty.email})")
        
        print()
    
    @app.cli.command()
    def test_auth():
        """Test faculty-only authentication"""
        from app.services.user_service import UserService
        
        print("🔐 Testing Faculty-Only Authentication")
        print("=" * 50)
        
        test_cases = [
            ('sanjeev.raghav@edubot.com', 'sanjeev123', 'Admin Faculty'),
            ('priya.sharma@edubot.com', 'priya123', 'Accounts Faculty'),
            ('rajesh.singh@edubot.com', 'rajesh123', 'Regular Faculty'),
            ('admin', 'admin123', 'Old Admin (should fail)'),
            ('nonexistent@edubot.com', 'password123', 'Non-existent (should fail)')
        ]
        
        for email, password, description in test_cases:
            result = UserService.authenticate_user(email, password)
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} {description}: {result['message']}")
            
            if result['success']:
                user = result['user']
                print(f"     → User: {user.name} ({user.role})")
        
        print("\n📋 Faculty Login Credentials:")
        print("Admin: sanjeev.raghav@edubot.com / sanjeev123")
        print("Accounts: priya.sharma@edubot.com / priya123")
        print("Accounts: amit.kumar@edubot.com / amit123")
        print("Faculty: rajesh.singh@edubot.com / rajesh123")
        print("Faculty: anita.verma@edubot.com / anita123")
        print("Faculty: vikas.gupta@edubot.com / vikas123")
        print("Faculty: sneha.patel@edubot.com / sneha123")
    
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
        from app.services.database_setup import DatabaseSetup
        
        # Initialize database using DatabaseSetup service
        success = DatabaseSetup.initialize_database()
        
        if success:
            app.logger.info("Database initialization completed successfully")
        else:
            app.logger.warning("Database initialization completed with warnings")
        
    except Exception as e:
        app.logger.error(f"Error initializing database: {str(e)}")
        # Don't raise exception to allow app to continue
        pass


def _ensure_schema(app):
    """
    Ensure newer columns exist on existing SQLite DBs.
    This project doesn't ship migrations, so we do safe ALTER TABLEs.
    """
    from sqlalchemy import inspect, text

    inspector = inspect(db.engine)

    def has_column(table: str, col: str) -> bool:
        try:
            return any(c.get('name') == col for c in inspector.get_columns(table))
        except Exception:
            return False

    # notifications: notification_type, priority
    if inspector.has_table('notifications'):
        if not has_column('notifications', 'notification_type'):
            db.session.execute(text("ALTER TABLE notifications ADD COLUMN notification_type VARCHAR(50) DEFAULT 'general'"))
        if not has_column('notifications', 'priority'):
            db.session.execute(text("ALTER TABLE notifications ADD COLUMN priority VARCHAR(20) DEFAULT 'medium'"))

    # results: created_by
    if inspector.has_table('results'):
        if not has_column('results', 'created_by'):
            db.session.execute(text("ALTER TABLE results ADD COLUMN created_by INTEGER"))

    # telegram_user_mappings: student_id nullable, add verified
    if inspector.has_table('telegram_user_mappings'):
        if not has_column('telegram_user_mappings', 'verified'):
            db.session.execute(text("ALTER TABLE telegram_user_mappings ADD COLUMN verified BOOLEAN DEFAULT 0"))
        # SQLite cannot ALTER COLUMN to drop NOT NULL; for older DBs, we tolerate NOT NULL by only creating mapping
        # after we know the student. New DBs will have nullable student_id.

    db.session.commit()


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
