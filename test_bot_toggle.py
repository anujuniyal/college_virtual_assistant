#!/usr/bin/env python3
"""
Test script for the bot toggle functionality
"""
import requests
import json
import time

# Base URL (adjust if running on different port)
BASE_URL = "http://localhost:5000"

def test_bot_status():
    """Test the bot status endpoint"""
    print("Testing bot status endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/admin/bot-status")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_bot_toggle(action):
    """Test the bot toggle endpoint"""
    print(f"\nTesting bot toggle with action: {action}")
    try:
        response = requests.post(
            f"{BASE_URL}/admin/toggle-bot",
            json={"action": action},
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    """Main test function"""
    print("=== Bot Toggle Functionality Test ===\n")
    
    # Test initial status
    print("1. Checking initial bot status...")
    initial_status = test_bot_status()
    
    if not initial_status:
        print("❌ Cannot connect to the application. Make sure it's running.")
        return
    
    print("\n2. Testing bot activation...")
    activate_result = test_bot_toggle("activate")
    
    if activate_result and activate_result.get("success"):
        print("✅ Activation request sent successfully")
        time.sleep(3)  # Wait for bot to start
        
        print("\n3. Checking status after activation...")
        status_after_activate = test_bot_status()
        
        print("\n4. Testing bot deactivation...")
        deactivate_result = test_bot_toggle("deactivate")
        
        if deactivate_result and deactivate_result.get("success"):
            print("✅ Deactivation request sent successfully")
            time.sleep(2)  # Wait for bot to stop
            
            print("\n5. Checking final status...")
            final_status = test_bot_status()
        else:
            print("❌ Deactivation failed")
    else:
        print("❌ Activation failed")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main()
