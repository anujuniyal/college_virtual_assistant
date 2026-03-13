#!/usr/bin/env python3
"""
Run Telegram Bot with Polling (No Webhook Required)
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
from app import create_app

class PollingBotRunner:
    def __init__(self):
        self.running = False
        self.bot_service = None
        self.polling_thread = None
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
    def start(self):
        """Start the bot service with polling"""
        try:
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
            self.bot_service = TelegramBotService()
            self.bot_service.bot_token = bot_token
            self.running = True
            
            # Test bot connection
            bot_info = self.bot_service.get_bot_info()
            if not bot_info:
                print("❌ Failed to connect to Telegram bot")
                return False
            
            print(f"✅ Connected to bot: @{bot_info['username']} ({bot_info['first_name']})")
            print("🔄 Bot is now running in polling mode...")
            print("📝 Send a message to your bot to test")
            print("⏹️  Press Ctrl+C to stop the bot")
            print("-" * 50)
            
            # Start polling in a separate thread
            self.polling_thread = threading.Thread(target=self._poll_messages)
            self.polling_thread.daemon = True
            self.polling_thread.start()
            
            # Keep the main thread alive
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
    
    def _poll_messages(self):
        """Poll for messages from Telegram"""
        import requests
        offset = 0
        
        while self.running:
            try:
                # Get updates from Telegram
                url = f"https://api.telegram.org/bot{self.bot_service.bot_token}/getUpdates"
                params = {
                    'offset': offset,
                    'timeout': 30,  # Long polling
                    'allowed_updates': ['message']
                }
                
                response = requests.get(url, params=params, timeout=35)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('ok'):
                        updates = result.get('result', [])
                        
                        for update in updates:
                            # Process each update with app context
                            try:
                                with self.app.app_context():
                                    self.bot_service.process_update(update)
                                    offset = update['update_id'] + 1
                            except Exception as e:
                                print(f"⚠️  Error processing update: {str(e)}")
                                offset = update['update_id'] + 1
                                continue
                                
                else:
                    print(f"⚠️  Polling error: {response.status_code}")
                    time.sleep(5)
                    
            except requests.exceptions.Timeout:
                continue  # Normal timeout, continue polling
            except Exception as e:
                print(f"⚠️  Polling error: {str(e)}")
                time.sleep(5)
                continue
    
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
            
            # Clean up app context
            try:
                self.app_context.pop()
                print("✅ App context cleaned up")
            except Exception as e:
                print(f"⚠️  Error cleaning up app context: {str(e)}")
            
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
    runner = PollingBotRunner()
    success = runner.start()
    
    if not success:
        print("❌ Bot failed to start properly")
        sys.exit(1)
    else:
        print("✅ Bot started successfully")
