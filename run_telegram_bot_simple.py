#!/usr/bin/env python3
"""
Simple Telegram Bot Polling (Minimal Dependencies)
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

class SimplePollingBot:
    def __init__(self):
        self.running = False
        self.bot_token = None
        self.polling_thread = None
        
    def start(self):
        """Start the bot service with minimal dependencies"""
        try:
            print("🤖 Starting Simple Telegram Bot (Polling Mode)...")
            print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print()
            
            # Get bot token
            self.bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
            if not self.bot_token:
                print("❌ TELEGRAM_BOT_TOKEN not found in environment variables")
                return False
            
            print(f"🔧 Bot Token: {self.bot_token[:10]}...{self.bot_token[-10:] if len(self.bot_token) > 20 else ''}")
            
            # Test bot connection
            bot_info = self.get_bot_info()
            if not bot_info:
                print("❌ Failed to connect to Telegram bot")
                return False
            
            print(f"✅ Connected to bot: @{bot_info['username']} ({bot_info['first_name']})")
            print("🔄 Bot is now running in simple polling mode...")
            print("📝 Send a message to your bot to test")
            print("⏹️  Press Ctrl+C to stop the bot")
            print("-" * 50)
            
            self.running = True
            
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
    
    def get_bot_info(self):
        """Get bot information"""
        try:
            import requests
            url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    return result.get('result')
            
            return None
            
        except Exception as e:
            print(f"❌ Error getting bot info: {str(e)}")
            return None
    
    def _poll_messages(self):
        """Poll for messages from Telegram"""
        import requests
        offset = 0
        
        while self.running:
            try:
                # Get updates from Telegram
                url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
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
                            # Process each update
                            try:
                                self._process_update(update)
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
    
    def _process_update(self, update):
        """Process a single update"""
        try:
            message = update.get('message', {})
            if not message:
                return
            
            chat_id = message.get('chat', {}).get('id')
            text = message.get('text', '')
            user = message.get('from', {})
            
            if not text or not chat_id:
                return
            
            print(f"📨 Message from {user.get('first_name', 'Unknown')} ({user.get('username', 'N/A')}): {text}")
            
            # Simple response logic
            response_text = self._generate_response(text)
            
            if response_text:
                self._send_message(chat_id, response_text)
                
        except Exception as e:
            print(f"⚠️  Error processing update: {str(e)}")
    
    def _generate_response(self, text):
        """Generate response for message"""
        text_lower = text.lower()
        
        if 'hello' in text_lower or 'hi' in text_lower:
            return "👋 Hello! I'm EduBot Assistant. How can I help you today?\n\nTry asking about:\n• Admission\n• Courses\n• Fees\n• Results\n• Help"
        
        elif 'admission' in text_lower:
            return "📚 *Admission Information*\n\nFor admission details, please visit our college website or contact the admission office.\n\n📞 Contact: +91-1234567890\n🌐 Website: www.college.edu"
        
        elif 'course' in text_lower or 'courses' in text_lower:
            return "📖 *Available Courses*\n\n• Computer Science\n• Information Technology\n• Electronics & Communication\n• Mechanical Engineering\n• Civil Engineering\n\nFor detailed syllabus, please visit our website."
        
        elif 'fee' in text_lower or 'fees' in text_lower:
            return "💰 *Fee Structure*\n\n• Tuition Fee: ₹50,000/year\n• Hostel Fee: ₹20,000/year\n• Other Fees: ₹10,000/year\n\nTotal: ₹80,000/year (approx)\n\nFor exact details, please contact the accounts department."
        
        elif 'result' in text_lower or 'results' in text_lower:
            return "📊 *Results*\n\nTo check your results:\n1. Visit our college portal\n2. Enter your roll number\n3. Select semester\n\n🔗 Portal: results.college.edu"
        
        elif 'help' in text_lower:
            return "❓ *Help*\n\nI can help you with information about:\n• 📚 Admissions\n• 📖 Courses\n• 💰 Fees\n• 📊 Results\n• 📞 Contact\n\nJust type any keyword to get started!"
        
        else:
            return f"🤔 I received: '{text}'\n\nType 'help' to see what I can assist you with!"
    
    def _send_message(self, chat_id, text):
        """Send message to Telegram"""
        try:
            import requests
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    print(f"✅ Message sent to {chat_id}")
                    return True
            
            print(f"❌ Failed to send message: {response.text}")
            return False
            
        except Exception as e:
            print(f"❌ Error sending message: {str(e)}")
            return False
    
    def stop(self):
        """Stop the bot service"""
        if self.running:
            print("🛑 Stopping bot service...")
            self.running = False
            
            try:
                # Cleanup webhook if needed
                import requests
                webhook_url = f"https://api.telegram.org/bot{self.bot_token}/deleteWebhook"
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
    runner = SimplePollingBot()
    success = runner.start()
    
    if not success:
        print("❌ Bot failed to start properly")
        sys.exit(1)
    else:
        print("✅ Bot started successfully")
