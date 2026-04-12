#!/usr/bin/env python3
"""
Test student verification message format
"""
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app
from app.chatbot.service import ChatbotService

def test_student_format():
    """Test student verification message format"""
    print("=== TESTING STUDENT VERIFICATION MESSAGE FORMAT ===")
    
    app = create_app()
    
    with app.app_context():
        chatbot = ChatbotService()
        
        # Test the verification message format
        print("Testing student verification message format...")
        
        # Check if the format has numbered options like visitor mode
        test_phone = "whatsapp:+test_user"
        
        try:
            # Test with a roll number that might exist
            response = chatbot.process_message("EDU25001", test_phone)
            print(f"Response format check:")
            print(f"Contains '1.' for Results: {'1.' in response or '1\u20e3' in response}")
            print(f"Contains '2.' for Notices: {'2.' in response or '2\u20e3' in response}")
            print(f"Contains numbered options: {'1.' in response and '2.' in response}")
            print(f"Response preview: {response[:200]}...")
        except Exception as e:
            print(f"Error: {e}")
        
        # Check the actual student greeting function
        print(f"\n=== CHECKING STUDENT GREETING FUNCTION ===")
        try:
            # This will show the format of the student greeting
            import inspect
            greet_student_source = inspect.getsource(chatbot._greet_student)
            print("Student greeting format:")
            print(greet_student_source[:500])
        except Exception as e:
            print(f"Error checking source: {e}")

if __name__ == "__main__":
    test_student_format()
