#!/usr/bin/env python3
"""
Database Setup Script
Initialize the database with environment-based configuration
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.factory import create_app
from app.services.user_service import UserService
from app.services.database_setup import DatabaseSetup


def main():
    """Main setup function"""
    print("🚀 Starting Database Setup...")
    print("=" * 50)
    
    # Create Flask app
    app = create_app()
    
    with app.app_context():
        # Validate configuration
        print("📋 Validating configuration...")
        config_result = DatabaseSetup.validate_configuration()
        if not config_result['success']:
            print(f"❌ Configuration validation failed: {config_result['message']}")
            print("\nPlease check your .env file and ensure all required variables are set.")
            return False
        
        print("✅ Configuration validation passed")
        
        # Initialize database
        print("\n🗄️  Initializing database...")
        success = DatabaseSetup.initialize_database()
        
        if not success:
            print("❌ Database initialization failed")
            return False
        
        print("✅ Database initialized successfully")
        
        # Show database info
        print("\n📊 Database Information:")
        info_result = DatabaseSetup.get_database_info()
        if info_result['success']:
            info = info_result['info']
            print(f"Users: {info['users']['total']} total")
            print(f"  - Admin: {info['users']['admin']}")
            print(f"  - Faculty: {info['users']['faculty']}")
            print(f"  - Accounts: {info['users']['accounts']}")
            print(f"  - Active: {info['users']['active']}")
            print(f"Students: {info['students']}")
            print(f"Faculty Records: {info['faculty_records']}")
        
        # Show login credentials
        print("\n🔑 Login Credentials:")
        print(f"Admin Username: {app.config['DEFAULT_ADMIN_USERNAME']}")
        print(f"Admin Password: {app.config['DEFAULT_ADMIN_PASSWORD']}")
        print(f"Admin Email: {app.config['DEFAULT_ADMIN_EMAIL']}")
        print(f"Admin Role: {app.config['DEFAULT_ADMIN_ROLE']}")
        
        print("\n🎉 Database setup completed successfully!")
        print("\nTo start the application:")
        print("python run_app.py")
        print("\nTo manage users:")
        print("flask list-users")
        print("flask create-user <username> <email> <password> <role>")
        print("flask validate-config")
        
        return True


def create_test_users():
    """Create additional test users"""
    app = create_app()
    
    with app.app_context():
        print("🧪 Creating test users...")
        
        test_users = [
            {
                'username': 'faculty',
                'email': 'faculty@edubot.com',
                'password': 'faculty123',
                'role': 'faculty'
            },
            {
                'username': 'accounts',
                'email': 'accounts@edubot.com',
                'password': 'accounts123',
                'role': 'accounts'
            }
        ]
        
        for user_data in test_users:
            # Check if user already exists
            existing = UserService.get_user_by_username(user_data['username'])
            if existing:
                print(f"ℹ️  User {user_data['username']} already exists")
                continue
            
            # Create user
            result = UserService.create_user(**user_data)
            if result['success']:
                print(f"✅ Created {user_data['role']} user: {user_data['username']}")
            else:
                print(f"❌ Failed to create {user_data['username']}: {result['message']}")
        
        print("\n📋 Test User Credentials:")
        for user_data in test_users:
            print(f"{user_data['role'].title()}: {user_data['username']} / {user_data['password']}")


def setup_specified_faculty():
    """Create the specified faculty users as requested"""
    app = create_app()
    
    with app.app_context():
        print("👥 Setting up specified faculty users...")
        
        from app.services.faculty_setup import FacultySetup
        result = FacultySetup.create_specified_faculty()
        
        if result['success']:
            print(f"✅ Successfully processed {result['total']} faculty users")
            
            if result['created']:
                print("\n🆕 Created Faculty Users:")
                for user in result['created']:
                    print(f"  - {user['name']} ({user['role']})")
                    print(f"    Email: {user['email']}")
                    print(f"    Password: {user['password']}")
                    print()
            
            if result['updated']:
                print("\n🔄 Updated Faculty Users:")
                for user in result['updated']:
                    print(f"  - {user['name']} ({user['role']})")
                    print(f"    Email: {user['email']}")
                    print(f"    Password: {user['password']}")
                    print()
            
            print("\n📋 Faculty Login Credentials:")
            all_users = result['created'] + result['updated']
            for user in all_users:
                print(f"{user['role'].title()}: {user['email']} / {user['password']}")
            
        else:
            print(f"❌ Error: {result['message']}")
            return False
        
        return True


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == '--create-test-users':
            create_test_users()
        elif sys.argv[1] == '--setup-faculty':
            success = setup_specified_faculty()
            if not success:
                sys.exit(1)
        else:
            print("Usage:")
            print("  python setup_database.py                    # Initialize database")
            print("  python setup_database.py --create-test-users  # Create test users")
            print("  python setup_database.py --setup-faculty      # Create specified faculty users")
    else:
        success = main()
        if not success:
            sys.exit(1)
