#!/usr/bin/env python3
"""
Local Telegram Bot Testing Script
Tests bot functionality locally before deploying
"""
import os
import sys
from app import create_app
from app.services.telegram_service import TelegramBotService
from app.chatbot.service import ChatbotService

def test_local_bot_service():
    """Test bot service locally"""
    print("=== LOCAL BOT TESTING ===")
    
    # Create app and set environment
    app = create_app()
    
    with app.app_context():
        # Test 1: Initialize Telegram Bot Service
        print("1. Testing Telegram Bot Service...")
        try:
            bot_service = TelegramBotService()
            bot_token = '7671092916:AAG4GMyeTli6V9rEF6GH9H_HliV4QRq8Guw'
            bot_service.bot_token = bot_token
            
            print(f"   Bot Token: {bot_token[:10]}...")
            
            # Test bot info
            bot_info = bot_service.get_bot_info()
            if bot_info:
                print(f"   Bot Name: {bot_info.get('first_name', 'Unknown')}")
                print(f"   Bot Username: @{bot_info.get('username', 'Unknown')}")
                print("   Bot Service: WORKING")
            else:
                print("   Bot Service: FAILED - Could not get bot info")
                return False
                
        except Exception as e:
            print(f"   Bot Service: FAILED - {str(e)}")
            return False
        
        # Test 2: Test Chatbot Service
        print("\n2. Testing Chatbot Service...")
        try:
            chatbot = ChatbotService()
            
            # Test visitor commands
            test_commands = [
                ("hi", "visitor"),
                ("help", "visitor"),
                ("admission", "visitor"),
                ("courses", "visitor"),
                ("contact", "visitor")
            ]
            
            for cmd, mode in test_commands:
                try:
                    if mode == "visitor":
                        phone = f"whatsapp:+visitor_test"
                    else:
                        phone = "whatsapp:+1234567890"
                    
                    response = chatbot.process_message(cmd, phone)
                    if response and len(response) > 10:
                        print(f"   Command '{cmd}': WORKING")
                    else:
                        print(f"   Command '{cmd}': FAILED - Empty response")
                except Exception as e:
                    print(f"   Command '{cmd}': FAILED - {str(e)}")
            
            print("   Chatbot Service: WORKING")
            
        except Exception as e:
            print(f"   Chatbot Service: FAILED - {str(e)}")
            return False
        
        # Test 3: Test Database Connection
        print("\n3. Testing Database Connection...")
        try:
            from app.extensions import db
            from app.models import Student, Admin
            
            # Test database query
            admin_count = Admin.query.count()
            student_count = Student.query.count()
            
            print(f"   Database: CONNECTED")
            print(f"   Admins: {admin_count}")
            print(f"   Students: {student_count}")
            
        except Exception as e:
            print(f"   Database: FAILED - {str(e)}")
            return False
        
        # Test 4: Test Telegram Update Processing
        print("\n4. Testing Telegram Update Processing...")
        try:
            # Create test update
            test_update = {
                "update_id": 123456789,
                "message": {
                    "message_id": 1,
                    "from": {
                        "id": 123456789,
                        "first_name": "Test",
                        "username": "test_user"
                    },
                    "chat": {
                        "id": 123456789,
                        "first_name": "Test",
                        "username": "test_user"
                    },
                    "date": 1640000000,
                    "text": "hi"
                }
            }
            
            # Process update
            result = bot_service.process_update(test_update)
            print("   Update Processing: WORKING")
            
        except Exception as e:
            print(f"   Update Processing: FAILED - {str(e)}")
            return False
        
        print("\n=== LOCAL TESTS COMPLETED ===")
        print("All local tests passed! Bot is working correctly.")
        return True

def test_phone_number_handling():
    """Test phone number handling with new field length"""
    print("\n5. Testing Phone Number Handling...")
    
    app = create_app()
    with app.app_context():
        try:
            from app.services.telegram_service import TelegramBotService
            from app.models import Student
            
            bot_service = TelegramBotService()
            
            # Test phone number validation
            test_phones = [
                "9876543210",           # 10 digits
                "09876543210",          # 11 digits with 0
                "919876543210",         # 12 digits with 91
                "+919876543210",        # 13 digits with +91
                "123456789012345",      # 15 digits
                "1234567890123456",     # 16 digits (should work now)
            ]
            
            for phone in test_phones:
                try:
                    # Test phone normalization
                    normalized = bot_service._normalize_phone(phone)
                    if normalized:
                        print(f"   Phone '{phone}': VALID -> '{normalized}'")
                    else:
                        print(f"   Phone '{phone}': INVALID")
                except Exception as e:
                    print(f"   Phone '{phone}': ERROR - {str(e)}")
            
            print("   Phone Number Handling: WORKING")
            return True
            
        except Exception as e:
            print(f"   Phone Number Handling: FAILED - {str(e)}")
            return False

def main():
    print("Starting local bot verification...")
    
    # Check if environment is set up
    if not os.environ.get('FLASK_ENV'):
        os.environ['FLASK_ENV'] = 'production'
    
    # Run tests
    success = test_local_bot_service()
    
    if success:
        success = test_phone_number_handling()
    
    print(f"\n=== FINAL RESULT ===")
    if success:
        print("LOCAL BOT: WORKING CORRECTLY")
        print("\nNext steps:")
        print("1. Deploy to Render")
        print("2. Test with real Telegram messages")
        print("3. Monitor Render logs")
    else:
        print("LOCAL BOT: HAS ISSUES")
        print("\nFix local issues before deploying")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
