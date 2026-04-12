#!/usr/bin/env python3
"""
Quick Bot Test - Simple verification of bot functionality
"""
import requests
import json

BOT_TOKEN = "7671092916:AAG4GMyeTli6V9rEF6GH9H_HliV4QRq8Guw"
RENDER_URL = "https://college-virtual-assistant.onrender.com"

def test_bot_token():
    """Test if bot token is valid"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data.get('result', {})
                print(f"BOT TOKEN: VALID")
                print(f"Bot Name: {bot_info.get('first_name', 'Unknown')}")
                print(f"Bot Username: @{bot_info.get('username', 'Unknown')}")
                return True
            else:
                print(f"BOT TOKEN: INVALID - {data.get('description', 'Unknown error')}")
                return False
        else:
            print(f"BOT TOKEN: ERROR - HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"BOT TOKEN: EXCEPTION - {str(e)}")
        return False

def test_render_service():
    """Test if Render service is running"""
    try:
        response = requests.get(RENDER_URL, timeout=10)
        if response.status_code in [200, 302]:
            print(f"RENDER SERVICE: RUNNING (HTTP {response.status_code})")
            return True
        else:
            print(f"RENDER SERVICE: ERROR - HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"RENDER SERVICE: EXCEPTION - {str(e)}")
        return False

def test_webhook():
    """Test webhook endpoint"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                webhook_info = data.get('result', {})
                webhook_url = webhook_info.get('url', '')
                
                if webhook_url:
                    print(f"WEBHOOK: CONFIGURED - {webhook_url}")
                else:
                    print(f"WEBHOOK: NOT CONFIGURED (Polling mode)")
                return True
            else:
                print(f"WEBHOOK: ERROR - {data.get('description', 'Unknown')}")
                return False
        else:
            print(f"WEBHOOK: ERROR - HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"WEBHOOK: EXCEPTION - {str(e)}")
        return False

def test_telegram_endpoint():
    """Test Telegram webhook endpoint"""
    try:
        url = f"{RENDER_URL}/telegram/webhook"
        
        # Create a test message
        test_data = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {"id": 123456789, "first_name": "Test"},
                "chat": {"id": 123456789, "first_name": "Test"},
                "date": 1640000000,
                "text": "hi"
            }
        }
        
        response = requests.post(url, json=test_data, timeout=10)
        
        if response.status_code == 200:
            print(f"TELEGRAM ENDPOINT: WORKING (HTTP {response.status_code})")
            return True
        else:
            print(f"TELEGRAM ENDPOINT: ERROR - HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"TELEGRAM ENDPOINT: EXCEPTION - {str(e)}")
        return False

def main():
    print("=== QUICK BOT VERIFICATION ===")
    print(f"Bot Token: {BOT_TOKEN[:10]}...")
    print(f"Render URL: {RENDER_URL}")
    print()
    
    tests = [
        ("Bot Token", test_bot_token),
        ("Render Service", test_render_service),
        ("Webhook Status", test_webhook),
        ("Telegram Endpoint", test_telegram_endpoint)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"Testing {name}...")
        result = test_func()
        results.append(result)
        print()
    
    passed = sum(results)
    total = len(results)
    
    print("=== SUMMARY ===")
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("BOT IS WORKING CORRECTLY!")
    else:
        print("BOT HAS ISSUES - Check failed tests above")
    
    print("\n=== NEXT STEPS ===")
    if passed == total:
        print("1. Test bot in Telegram: Send 'hi' to your bot")
        print("2. Try commands: 'help', 'admission', 'courses'")
        print("3. Test student verification with phone sharing")
    else:
        print("1. Fix failed tests above")
        print("2. Check Render logs for errors")
        print("3. Verify environment variables")

if __name__ == "__main__":
    main()
