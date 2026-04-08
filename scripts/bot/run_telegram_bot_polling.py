#!/usr/bin/env python3
"""
Simple Telegram Bot Polling Service - Student/Visitor Mode
"""
import os
import sys
import time
import signal
from datetime import datetime

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

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from app import create_app
from app.services.telegram_service import TelegramBotService

def main():
    """Main bot function"""
    try:
        # Create Flask app and push context
        app = create_app()
        app.app_context().push()
        
        print("🤖 Starting Telegram Bot Service (Polling Mode)...")
        print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Get bot token
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            print("❌ TELEGRAM_BOT_TOKEN not found in environment variables")
            return False
        
        print(f"🔧 Bot Token: {bot_token[:10]}...{bot_token[-10:] if len(bot_token) > 20 else ''}")
        
        # Initialize bot service
        bot_service = TelegramBotService()
        bot_service.bot_token = bot_token
        
        # Test bot connection
        bot_info = bot_service.get_bot_info()
        if not bot_info:
            print("❌ Failed to connect to Telegram API")
            return False
        
        print(f"✅ Connected to bot: {bot_info.get('first_name')} (@{bot_info.get('username')})")
        
        print("✅ Bot service initialized successfully")
        print("✅ Polling mode activated")
        print("🔄 Bot is now running and listening for messages...")
        print("📝 Send a message to @edubot_assistant_bot to test")
        print("⏹️  Press Ctrl+C to stop the bot")
        print("-" * 50)
        
        # Polling loop
        last_update_id = 0
        running = True
        
        while running:
            try:
                # Get updates from Telegram
                import requests
                url = f"https://api.telegram.org/bot{bot_service.bot_token}/getUpdates"
                params = {
                    'offset': last_update_id + 1 if last_update_id else None,
                    'timeout': 30,  # Long polling
                    'allowed_updates': ['message']
                }
                
                response = requests.get(url, params=params, timeout=35)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('ok'):
                        updates = result.get('result', [])
                        
                        for update in updates:
                            # Process the update
                            try:
                                result = bot_service.process_update(update)
                                if result:
                                    print(f"✅ Processed update {update.get('update_id')}")
                                last_update_id = update.get('update_id', 0)
                            except Exception as e:
                                print(f"❌ Error processing update: {str(e)}")
                    else:
                        error_desc = result.get('description', 'Unknown error')
                        print(f"❌ Updates error: {error_desc}")
                else:
                    print(f"❌ HTTP error getting updates: {response.status_code}")
                
                # Small delay to prevent overwhelming the API
                time.sleep(1)
                
            except KeyboardInterrupt:
                print("\n⏹️  KeyboardInterrupt received")
                running = False
                break
            except requests.exceptions.Timeout:
                print("⚠️  Timeout getting updates, retrying...")
                continue
            except requests.exceptions.ConnectionError:
                print("⚠️  Connection error getting updates, retrying...")
                time.sleep(5)
                continue
            except Exception as e:
                print(f"❌ Polling error: {str(e)}")
                time.sleep(5)
        
        print(f"📅 Stopped at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("👋 Bot service stopped successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error in bot service: {str(e)}")
        return False

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\n📡 Received signal {signum}")
    sys.exit(0)

if __name__ == "__main__":
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the bot
    success = main()
    
    if not success:
        print("❌ Bot failed to start properly")
        sys.exit(1)
    else:
        print("✅ Bot started successfully")
