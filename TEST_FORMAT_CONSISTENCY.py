#!/usr/bin/env python3
"""
Test message format consistency across all bot responses
"""
import sys
import os

# Add app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app
from app.chatbot.service import ChatbotService

def test_format_consistency():
    """Test that all message formats use consistent numbering"""
    print("=== TESTING MESSAGE FORMAT CONSISTENCY ===")
    
    app = create_app()
    
    with app.app_context():
        chatbot = ChatbotService()
        test_phone = "whatsapp:+test_user"
        
        # Test visitor greeting
        print("\n1. Testing visitor greeting format...")
        try:
            visitor_response = chatbot._greet_visitor(test_phone)
            has_emoji_numbers = '1️⃣' in visitor_response or '2️⃣' in visitor_response
            has_plain_numbers = '1.' in visitor_response and '2.' in visitor_response
            print(f"   Emoji numbers: {has_emoji_numbers}")
            print(f"   Plain numbers: {has_plain_numbers}")
            print(f"   Format: {'EMOJI' if has_emoji_numbers else 'PLAIN' if has_plain_numbers else 'UNKNOWN'}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test student verification message
        print("\n2. Testing student verification format...")
        try:
            # This will show verification message format
            response = chatbot.process_message("EDU25001", test_phone)
            has_emoji_numbers = '1️⃣' in response or '2️⃣' in response
            has_plain_numbers = '1.' in response and '2.' in response
            print(f"   Emoji numbers: {has_emoji_numbers}")
            print(f"   Plain numbers: {has_plain_numbers}")
            print(f"   Format: {'EMOJI' if has_emoji_numbers else 'PLAIN' if has_plain_numbers else 'UNKNOWN'}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test student help
        print("\n3. Testing student help format...")
        try:
            # Mock student_id for testing
            help_response = chatbot._show_help_student(test_phone, 1)
            has_emoji_numbers = '1️⃣' in help_response or '2️⃣' in help_response
            has_plain_numbers = '1.' in help_response and '2.' in help_response
            print(f"   Emoji numbers: {has_emoji_numbers}")
            print(f"   Plain numbers: {has_plain_numbers}")
            print(f"   Format: {'EMOJI' if has_emoji_numbers else 'PLAIN' if has_plain_numbers else 'UNKNOWN'}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test admission info
        print("\n4. Testing admission info format...")
        try:
            admission_response = chatbot._admission_info(test_phone)
            has_emoji_numbers = '1️⃣' in admission_response or '2️⃣' in admission_response
            has_plain_numbers = '1.' in admission_response and '2.' in admission_response
            print(f"   Emoji numbers: {has_emoji_numbers}")
            print(f"   Plain numbers: {has_plain_numbers}")
            print(f"   Format: {'EMOJI' if has_emoji_numbers else 'PLAIN' if has_plain_numbers else 'UNKNOWN'}")
        except Exception as e:
            print(f"   Error: {e}")
        
        print("\n=== CONSISTENCY CHECK ===")
        print("All responses should use the SAME format (either ALL emoji or ALL plain numbers)")
        print("If you see mixed formats, that's the issue causing confusion.")

if __name__ == "__main__":
    test_format_consistency()
