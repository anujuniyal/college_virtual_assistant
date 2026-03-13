#!/usr/bin/env python3
"""
Test Telegram Bot Notifications
"""
import os
import sys
from datetime import datetime

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app

def test_notification():
    """Test sending a notification to admin"""
    app = create_app()
    
    with app.app_context():
        bot_token = app.config.get('TELEGRAM_BOT_TOKEN')
        admin_chat_id = os.environ.get('ADMIN_TELEGRAM_CHAT_ID')
        
        print(f"Bot Token: {bot_token[:10]}...{bot_token[-10:] if bot_token else 'None'}")
        print(f"Admin Chat ID: {admin_chat_id}")
        
        if not bot_token:
            print("❌ TELEGRAM_BOT_TOKEN not configured")
            return False
            
        if not admin_chat_id:
            print("❌ ADMIN_TELEGRAM_CHAT_ID not configured")
            return False
        
        try:
            import requests
            
            # Test activation notification
            message = f"🤖 *Test Notification*\n\n👤 Admin: Test User\n🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n🔄 Mode: Testing\n\n✅ This is a test notification from EduBot!"
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                'chat_id': admin_chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                print("✅ Test notification sent successfully!")
                print(f"Message ID: {result.get('result', {}).get('message_id')}")
                return True
            else:
                print(f"❌ Failed to send notification: {result.get('description')}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending notification: {str(e)}")
            return False

if __name__ == "__main__":
    print("🧪 Testing Telegram Bot Notifications")
    print("=" * 40)
    success = test_notification()
    
    if success:
        print("\n✅ Notification test passed!")
        print("You should receive a test message in Telegram.")
    else:
        print("\n❌ Notification test failed!")
        print("Check your bot token and chat ID configuration.")
