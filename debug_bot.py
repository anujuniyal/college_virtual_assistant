#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import requests

load_dotenv()
token = os.environ.get('TELEGRAM_BOT_TOKEN')

# Delete webhook temporarily
url = f'https://api.telegram.org/bot{token}/deleteWebhook'
response = requests.get(url)
result = response.json()
print('Webhook deleted:', result.get('description', 'Unknown'))

# Get updates
url = f'https://api.telegram.org/bot{token}/getUpdates'
response = requests.get(url)
result = response.json()

print('\nBot Updates:')
if result.get('ok'):
    updates = result.get('result', [])
    if updates:
        for update in updates[-3:]:  # Show last 3 updates
            message = update.get('message', {})
            chat = message.get('chat', {})
            user = message.get('from', {})
            text = message.get('text', '')
            chat_id = chat.get('id')
            user_name = user.get('first_name', 'Unknown')
            print(f'Chat ID: {chat_id} - User: {user_name} - Message: {text}')
            
            # Send a test response to this chat
            if chat_id and text:
                send_url = f'https://api.telegram.org/bot{token}/sendMessage'
                send_data = {
                    'chat_id': chat_id,
                    'text': f'✅ Bot is working! You said: "{text}"\n\nTry these commands:\n• "Help"\n• "Results"\n• "Fees"\n• "Notifications"'
                }
                send_response = requests.post(send_url, json=send_data)
                send_result = send_response.json()
                if send_result.get('ok'):
                    print(f'✅ Test message sent to {user_name}')
                else:
                    print(f'❌ Failed to send: {send_result.get("description")}')
    else:
        print('No recent updates found')
        print('Please send a message to @edubot_assistant_bot first!')

# Set webhook back
webhook_url = 'https://fae2-2409-4090-b098-201b-47c1-a9d3-5f79-7200.ngrok-free.app/telegram/webhook'
url = f'https://api.telegram.org/bot{token}/setWebhook'
data = {'url': webhook_url, 'allowed_updates': ['message']}
response = requests.post(url, json=data)
result = response.json()
print(f'\nWebhook restored: {result.get("description", "Unknown")}')
