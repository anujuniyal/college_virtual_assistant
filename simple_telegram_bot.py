#!/usr/bin/env python3
"""
Simple Telegram Bot Polling Service
"""
import os
import sys
import time
import signal
import requests
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

class SimpleTelegramBot:
    def __init__(self):
        self.bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.running = False
        self.last_update_id = 0
        
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
        
        print(f"🤖 Bot token loaded: {self.bot_token[:10]}...{self.bot_token[-10:]}")
    
    def test_connection(self):
        """Test bot connection"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    bot_info = result['result']
                    print(f"✅ Connected to bot: {bot_info['first_name']} (@{bot_info['username']})")
                    return True
                else:
                    print(f"❌ Bot error: {result.get('description')}")
                    return False
            else:
                print(f"❌ HTTP error: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Connection error: {str(e)}")
            return False
    
    def send_message(self, chat_id, text):
        """Send a message to a chat"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    print(f"✅ Message sent to {chat_id}")
                    return True
                else:
                    print(f"❌ Send error: {result.get('description')}")
                    return False
            else:
                print(f"❌ HTTP error: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Send error: {str(e)}")
            return False
    
    def get_updates(self):
        """Get updates from Telegram"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
            params = {
                'offset': self.last_update_id + 1 if self.last_update_id else None,
                'timeout': 30  # Long polling
            }
            response = requests.get(url, params=params, timeout=35)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    updates = result.get('result', [])
                    return updates
                else:
                    print(f"❌ Updates error: {result.get('description')}")
                    return []
            else:
                print(f"❌ HTTP error: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Updates error: {str(e)}")
            return []
    
    def process_message(self, update):
        """Process a message update"""
        try:
            message = update.get('message', {})
            if not message:
                return
            
            chat_id = message.get('chat', {}).get('id')
            text = message.get('text', '')
            user = message.get('from', {})
            user_name = user.get('first_name', 'User')
            
            print(f"📩 Message from {user_name} ({chat_id}): {text}")
            
            # Simple echo response
            if text:
                response_text = f"🤖 Hello {user_name}!\\n\\nYou said: {text}\\n\\nBot is working! 🎉"
                self.send_message(chat_id, response_text)
            
            # Update the last processed update ID
            self.last_update_id = update.get('update_id', 0)
            
        except Exception as e:
            print(f"❌ Message processing error: {str(e)}")
    
    def start_polling(self):
        """Start polling for messages"""
        print("🔄 Starting message polling...")
        print("📝 Send a message to @edubot_assistant_bot to test")
        print("⏹️  Press Ctrl+C to stop the bot")
        print("-" * 50)
        
        self.running = True
        
        while self.running:
            try:
                updates = self.get_updates()
                
                for update in updates:
                    self.process_message(update)
                
                # Small delay to prevent overwhelming the API
                time.sleep(1)
                
            except KeyboardInterrupt:
                print("\\n⏹️  KeyboardInterrupt received")
                break
            except Exception as e:
                print(f"❌ Polling error: {str(e)}")
                time.sleep(5)  # Wait before retrying
    
    def stop(self):
        """Stop the bot"""
        print("🛑 Stopping bot...")
        self.running = False

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\\n📡 Received signal {signum}")
    if 'bot' in globals():
        bot.stop()
    sys.exit(0)

if __name__ == "__main__":
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🤖 Simple Telegram Bot Starting...")
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Create and start bot
        bot = SimpleTelegramBot()
        
        # Test connection
        if not bot.test_connection():
            print("❌ Failed to connect to Telegram API")
            sys.exit(1)
        
        # Start polling
        bot.start_polling()
        
    except Exception as e:
        print(f"❌ Bot startup error: {str(e)}")
        sys.exit(1)
    
    print(f"📅 Stopped at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("👋 Bot stopped successfully")
