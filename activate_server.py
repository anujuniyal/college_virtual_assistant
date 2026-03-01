#!/usr/bin/env python3
"""
EduBot Server Activation Script
Activates Flask server and Telegram bot with ngrok
"""

import os
import sys
import time
import subprocess
import requests
import threading
from pathlib import Path

class ServerActivator:
    def __init__(self):
        self.ngrok_url = None
        self.ngrok_process = None
        self.flask_process = None
        self.bot_token = "7671092916:AAG4GMyeTli6V9rEF6GH9H_HliV4QRq8Guw"
        
    def print_banner(self):
        """Print activation banner"""
        print("🚀 EDUBOT SERVER ACTIVATOR")
        print("=" * 50)
        print("🤖 Starting EduBot Server & Telegram Bot")
        print("📡 Setting up ngrok for public access")
        print("🔗 Configuring Telegram webhook")
        print("=" * 50)
    
    def check_requirements(self):
        """Check if all requirements are met"""
        print("\n🔍 CHECKING REQUIREMENTS...")
        
        # Check ngrok
        if not os.path.exists("ngrok.exe"):
            print("❌ ngrok.exe not found!")
            print("📥 Please download ngrok from: https://ngrok.com/download")
            return False

        # Check Python modules
        try:
            import flask
            import requests
            print("✅ Python modules available")
        except ImportError as e:
            print(f"❌ Missing Python module: {e}")
            print("📦 Run: pip install -r requirements.txt")
            return False

        # Check environment
        if os.path.exists(".env"):
            print("✅ Environment file found")
        else:
            print("⚠️ No .env file found (using defaults)")

        print("✅ All requirements met!")
        return True

    def _get_current_ngrok_url(self):
        """Fetch current public ngrok URL from the local ngrok API."""
        try:
            response = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=5)
            if response.status_code != 200:
                return None
            data = response.json()
            if not data.get("tunnels"):
                return None
            return data["tunnels"][0].get("public_url")
        except Exception:
            return None

    def _get_telegram_webhook_info(self):
        """Fetch current Telegram webhook info."""
        try:
            response = requests.get(
                f"https://api.telegram.org/bot{self.bot_token}/getWebhookInfo",
                timeout=10,
            )
            if response.status_code != 200:
                return None
            return response.json().get("result")
        except Exception:
            return None
    
    def start_ngrok(self):
        """Start ngrok in background"""
        print("\n🚀 STARTING NGROK...")
        
        try:
            # Start ngrok
            self.ngrok_process = subprocess.Popen(
                ["ngrok.exe", "http", "5000"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            
            # Wait for ngrok to start
            time.sleep(5)
            
            # Get ngrok URL
            last_error = None
            for _ in range(30):
                try:
                    response = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("tunnels"):
                            tunnel = data["tunnels"][0]
                            self.ngrok_url = tunnel["public_url"]
                            print(f"✅ ngrok URL: {self.ngrok_url}")
                            return True
                except Exception as e:
                    last_error = str(e)
                time.sleep(1)
            
            print("❌ Failed to get ngrok URL")
            if last_error:
                print(f"❌ Last error: {last_error}")
            return False
            
        except Exception as e:
            print(f"❌ Error starting ngrok: {str(e)}")
            return False
    
    def start_flask_server(self):
        """Start Flask server in background"""
        print("\n🚀 STARTING FLASK SERVER...")
        
        try:
            # Set environment variables
            os.environ["FLASK_ENV"] = "production"
            
            # Start Flask server
            self.flask_process = subprocess.Popen(
                [sys.executable, "wsgi.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            
            # Wait for server to start
            time.sleep(2)
            
            # Check if server is running
            try:
                response = requests.get("http://localhost:5000/login", timeout=5)
                if response.status_code == 200:
                    print("✅ Flask server started successfully")
                    return True
            except:
                pass
            
            print("❌ Failed to start Flask server")
            return False
            
        except Exception as e:
            print(f"❌ Error starting Flask server: {str(e)}")
            return False
    
    def set_telegram_webhook(self):
        """Set Telegram webhook"""
        print("\n🔗 SETTING UP TELEGRAM WEBHOOK...")
        
        try:
            webhook_url = f"{self.ngrok_url}/webhook/telegram"
            
            response = requests.post(
                f"https://api.telegram.org/bot{self.bot_token}/setWebhook",
                json={
                    "url": webhook_url,
                    "allowed_updates": ["message"],
                    "drop_pending_updates": True,
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    print("✅ Telegram webhook set successfully!")
                    print(f"🤖 Bot is ready at: {webhook_url}")
                    return True
                else:
                    print(f"❌ Webhook error: {result.get('description')}")
            else:
                print(f"❌ HTTP error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error setting webhook: {str(e)}")
        
        return False
    
    def test_bot(self):
        """Test the bot functionality"""
        print("\n🧪 TESTING BOT FUNCTIONALITY...")
        
        try:
            webhook_url = f"{self.ngrok_url}/webhook/telegram"
            
            # Send test message
            test_message = {
                "message": {
                    "chat": {"id": 123456},
                    "from": {"id": 7229077719},
                    "text": "hi"
                }
            }
            
            response = requests.post(
                webhook_url,
                json=test_message,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Bot test successful!")
                return True
            else:
                print(f"⚠️ Bot test status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error testing bot: {str(e)}")
        
        return False
    
    def display_status(self):
        """Display final status"""
        print("\n🎉 ACTIVATION COMPLETE!")
        print("=" * 50)
        print(f"🌐 Flask Server: http://localhost:5000")
        print(f"📡 ngrok URL: {self.ngrok_url}")
        print(f"🤖 Telegram Bot: @edubot_assistant_bot")
        print(f"📱 Webhook: {self.ngrok_url}/webhook/telegram")
        print("=" * 50)
        
        print("\n📱 HOW TO USE YOUR BOT:")
        print("1. 📱 Open Telegram")
        print("2. 🔍 Search: @edubot_assistant_bot")
        print("3. 📤 Send: register EDU20240051")
        print("4. 🔢 Use numbers 1-6 for services")
        print("   1 - View Results")
        print("   2 - Check Fees")
        print("   3 - Get Notices")
        print("   4 - Search Faculty")
        print("   5 - Register Complaint")
        print("   6 - Logout")
        
        print("\n🌐 WEB INTERFACE:")
        print(f"📋 Login: http://localhost:5000/login")
        print("👤 Username: admin")
        print("🔒 Password: admin123")
        print("📁 Upload: /admin/upload")
        
        print("\n⚠️ IMPORTANT:")
        print("📋 Keep this window open to maintain services")
        print("🔄 Press Ctrl+C to stop all services")
        print("📋 Both ngrok and Flask will close when you exit")
    
    def monitor_services(self):
        """Monitor running services"""
        print("\n📡 MONITORING SERVICES...")
        print("🔄 Services are running. Press Ctrl+C to stop.")
        
        try:
            while True:
                time.sleep(10)

                # If ngrok URL changed (or Telegram webhook points elsewhere), reset the webhook.
                current_ngrok_url = self._get_current_ngrok_url()
                if current_ngrok_url and current_ngrok_url != self.ngrok_url:
                    print(f"\n🔄 ngrok URL changed: {self.ngrok_url} -> {current_ngrok_url}")
                    self.ngrok_url = current_ngrok_url
                    self.set_telegram_webhook()

                webhook_info = self._get_telegram_webhook_info()
                if webhook_info:
                    expected_webhook = f"{self.ngrok_url}/webhook/telegram" if self.ngrok_url else None
                    current_webhook = webhook_info.get("url")
                    if expected_webhook and current_webhook != expected_webhook:
                        print(f"\n🔄 Telegram webhook mismatch:\n   Current:  {current_webhook}\n   Expected: {expected_webhook}")
                        self.set_telegram_webhook()
                
                # Check if processes are still running
                if self.ngrok_process.poll() is not None:
                    print("❌ ngrok process stopped!")
                    break
                    
                if self.flask_process.poll() is not None:
                    print("❌ Flask server stopped!")
                    break
                    
        except KeyboardInterrupt:
            print("\n🛑 STOPPING SERVICES...")
        
        # Stop processes
        if self.ngrok_process:
            self.ngrok_process.terminate()
        if self.flask_process:
            self.flask_process.terminate()
        
        print("✅ All services stopped")
    
    def activate(self):
        """Main activation method"""
        self.print_banner()
        
        # Check requirements
        if not self.check_requirements():
            print("\n❌ ACTIVATION FAILED!")
            return False
        
        # Start services
        if not self.start_ngrok():
            print("\n❌ NGROK FAILED!")
            return False
        
        if not self.start_flask_server():
            print("\n❌ FLASK SERVER FAILED!")
            return False
        
        # Set webhook
        if not self.set_telegram_webhook():
            print("\n❌ WEBHOOK SETUP FAILED!")
            return False
        
        # Test bot
        self.test_bot()
        
        # Display status
        self.display_status()
        
        # Monitor services
        self.monitor_services()
        
        return True

def main():
    """Main function"""
    activator = ServerActivator()
    
    try:
        success = activator.activate()
        if success:
            print("\n🎉 ACTIVATION COMPLETED SUCCESSFULLY!")
        else:
            print("\n❌ ACTIVATION FAILED!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 ACTIVATION CANCELLED!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
