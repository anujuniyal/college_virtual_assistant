#!/usr/bin/env python3
"""
Activate Telegram Bot Webhook
"""
import os
import sys
import requests

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # If python-dotenv is not installed, try to load .env manually
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

from app.services.telegram_service import TelegramBotService

def test_bot_token(bot_token):
    """Test if bot token is valid"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                bot_info = result['result']
                print(f"✅ Bot connected successfully!")
                print(f"   Bot name: {bot_info['first_name']}")
                print(f"   Bot username: @{bot_info['username']}")
                return True
            else:
                print(f"❌ Bot error: {result.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing bot: {str(e)}")
        return False

def activate_webhook(bot_token, webhook_url):
    """Activate Telegram bot webhook"""
    try:
        bot_service = TelegramBotService()
        success = bot_service.initialize(bot_token, webhook_url)
        
        if success:
            print(f"✅ Webhook activated successfully!")
            print(f"   Webhook URL: {webhook_url}")
            return True
        else:
            print(f"❌ Failed to activate webhook")
            return False
            
    except Exception as e:
        print(f"❌ Error activating webhook: {str(e)}")
        return False

def main():
    """Main activation function"""
    print("🤖 Telegram Bot Activation")
    print("=" * 40)
    
    # Get bot token
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN environment variable not set")
        print("\nTo set up your bot:")
        print("1. Talk to @BotFather on Telegram")
        print("2. Use /newbot command")
        print("3. Follow the instructions")
        print("4. Copy the bot token")
        print("5. Set environment variable: export TELEGRAM_BOT_TOKEN=your_token")
        return False
    
    # Get webhook URL
    webhook_url = os.environ.get('PUBLIC_BASE_URL')
    if not webhook_url:
        # Default to local development (requires tunnel)
        webhook_url = "https://your-app-url.com/telegram/webhook"
        print("⚠️  PUBLIC_BASE_URL not set")
        print(f"   Using default: {webhook_url}")
        print("   For local development, use ngrok or similar tunnel")
    
    # Ensure webhook URL ends with /telegram/webhook
    if not webhook_url.endswith('/telegram/webhook'):
        webhook_url = webhook_url.rstrip('/') + '/telegram/webhook'
    
    print(f"🔧 Bot Token: {bot_token[:10]}...{bot_token[-10:] if len(bot_token) > 20 else ''}")
    print(f"🔧 Webhook URL: {webhook_url}")
    print()
    
    # Test bot token
    print("1️⃣ Testing bot token...")
    if not test_bot_token(bot_token):
        return False
    
    print()
    
    # Activate webhook
    print("2️⃣ Activating webhook...")
    if not activate_webhook(bot_token, webhook_url):
        return False
    
    print()
    print("🎉 Bot activation completed successfully!")
    print("\nNext steps:")
    print("- Your bot is now ready to receive messages")
    print("- Test by sending a message to your bot on Telegram")
    print("- Check logs for any errors")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
