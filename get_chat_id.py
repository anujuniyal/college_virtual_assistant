#!/usr/bin/env python3
"""
Get Your Telegram Chat ID
"""
import os
import sys
import time

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def get_chat_id():
    """Get the chat ID by checking recent updates"""
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not configured")
        return None
    
    try:
        import requests
        
        print("🔍 Getting your chat ID...")
        print("📝 Please send ANY message to @edubot_assistant_bot")
        print("⏳ Waiting for your message...")
        
        # Wait a moment for you to send a message
        time.sleep(3)
        
        # Get updates
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        response = requests.get(url, timeout=10)
        result = response.json()
        
        if result.get('ok'):
            updates = result.get('result', [])
            
            if updates:
                latest_update = updates[-1]
                message = latest_update.get('message', {})
                chat = message.get('chat', {})
                user = message.get('from', {})
                
                chat_id = chat.get('id')
                chat_type = chat.get('type')
                username = chat.get('username', user.get('username', 'Unknown'))
                
                print(f"\n✅ Found your chat details:")
                print(f"📱 Chat ID: {chat_id}")
                print(f"👤 Username: @{username}")
                print(f"💬 Chat Type: {chat_type}")
                print(f"📅 Date: {message.get('date', 'Unknown')}")
                
                if message.get('text'):
                    print(f"💭 Your message: {message.get('text')}")
                
                print(f"\n🔧 Add this to your .env file:")
                print(f"ADMIN_TELEGRAM_CHAT_ID={chat_id}")
                
                return chat_id
            else:
                print("❌ No recent messages found")
                print("📝 Please send a message to @edubot_assistant_bot and try again")
                return None
        else:
            print(f"❌ Error getting updates: {result.get('description')}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

if __name__ == "__main__":
    print("🔍 Get Your Telegram Chat ID")
    print("=" * 40)
    print("📝 Step 1: Open Telegram and find @edubot_assistant_bot")
    print("📝 Step 2: Send any message to the bot")
    print("📝 Step 3: Run this script again")
    print("📝 Step 4: Copy the chat ID to your .env file")
    print("=" * 40)
    
    chat_id = get_chat_id()
    
    if chat_id:
        print(f"\n✅ Success! Your chat ID is: {chat_id}")
    else:
        print("\n❌ Could not get chat ID. Make sure you sent a message to the bot.")
