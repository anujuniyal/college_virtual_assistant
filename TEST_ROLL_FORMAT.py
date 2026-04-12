#!/usr/bin/env python3
"""
Test new roll number format EDU25001
"""
import sys
import os
import re

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app
from app.chatbot.service import ChatbotService

def test_roll_format():
    """Test new roll number format"""
    print("=== TESTING ROLL NUMBER FORMAT ===")
    
    app = create_app()
    
    with app.app_context():
        chatbot = ChatbotService()
        
        # Test cases
        test_cases = [
            "EDU25001",
            "edu25001", 
            "EDU12345",
            "register EDU25001",
            "verify EDU25001",
            "roll: EDU25001",
            "EDU2025001",  # Old format
            "EDU1234",    # Too short
            "EDU123456"   # Too long
        ]
        
        for test_input in test_cases:
            print(f"\nTesting: '{test_input}'")
            
            # Test the regex pattern
            roll_match = re.search(r'EDU\d{5}', test_input, re.IGNORECASE)
            if roll_match:
                roll_number = roll_match.group(0).upper()
                print(f"  ✅ Matched: {roll_number}")
            else:
                print(f"  ❌ No match")
        
        # Test with actual chatbot service
        print(f"\n=== TESTING WITH CHATBOT SERVICE ===")
        test_phone = "whatsapp:+test_user"
        
        try:
            response = chatbot.process_message("EDU25001", test_phone)
            print(f"EDU25001 Response: {response[:100]}...")
        except Exception as e:
            print(f"Error: {e}")
        
        try:
            response = chatbot.process_message("register EDU25001", test_phone)
            print(f"register EDU25001 Response: {response[:100]}...")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_roll_format()
