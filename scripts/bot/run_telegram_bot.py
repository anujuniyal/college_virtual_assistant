#!/usr/bin/env python3
"""
Run Telegram Bot Service
"""
import os
import sys
import time
import signal
import threading
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

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.telegram_service import TelegramBotService

class BotRunner:
    def __init__(self):
        self.running = False
        self.bot_service = None
        
    def start(self):
        """Start the bot service"""
        try:
            print("🤖 Starting Telegram Bot Service...")
            print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print()
            
            # Get bot token
            bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
            if not bot_token:
                print("❌ TELEGRAM_BOT_TOKEN not found in environment variables")
                return False
            
            # Get webhook URL
            webhook_url = os.environ.get('PUBLIC_BASE_URL', 'http://localhost:5000')
            if not webhook_url.endswith('/telegram/webhook'):
                webhook_url = webhook_url.rstrip('/') + '/telegram/webhook'
            
            print(f"🔧 Bot Token: {bot_token[:10]}...{bot_token[-10:] if len(bot_token) > 20 else ''}")
            print(f"🌐 Webhook URL: {webhook_url}")
            
            # Initialize bot service
            self.bot_service = TelegramBotService()
            self.running = True
            
            # Set up webhook
            success = self.bot_service.initialize(bot_token, webhook_url)
            if not success:
                print("❌ Failed to initialize bot webhook")
                return False
            
            print("✅ Bot service initialized successfully")
            print("✅ Webhook set up successfully")
            print("🔄 Bot is now running and listening for messages...")
            print("📝 Send a message to your bot to test")
            print("⏹️  Press Ctrl+C to stop the bot")
            print("-" * 50)
            
            # Keep the bot running
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n⏹️  KeyboardInterrupt received")
            self.stop()
        except Exception as e:
            print(f"❌ Error in bot service: {str(e)}")
            self.stop()
            return False
        
        return True
            
    def stop(self):
        """Stop the bot service"""
        if self.running:
            print("🛑 Stopping bot service...")
            self.running = False
            
            if self.bot_service:
                try:
                    # Cleanup webhook if needed
                    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
                    if bot_token:
                        import requests
                        webhook_url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
                        requests.post(webhook_url, timeout=10)
                        print("✅ Webhook deleted")
                except Exception as e:
                    print(f"⚠️  Error cleaning up webhook: {str(e)}")
            
            print(f"📅 Stopped at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("👋 Bot service stopped successfully")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\n📡 Received signal {signum}")
    if 'runner' in globals():
        runner.stop()
    sys.exit(0)

if __name__ == "__main__":
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start bot runner
    runner = BotRunner()
    success = runner.start()
    
    if not success:
        print("❌ Bot failed to start properly")
        sys.exit(1)
    else:
        print("✅ Bot started successfully")
