#!/usr/bin/env python3
"""
Test script to verify predefined info integration with bot service
"""
import sys
import os

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.chatbot.service import ChatbotService
from app.models import PredefinedInfo, Admin
from app.extensions import db

def test_predefined_info_integration():
    """Test that bot fetches info from database and updates in real-time"""
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing Predefined Info Integration")
        print("=" * 50)
        
        # Initialize chatbot service
        bot_service = ChatbotService()
        
        # Test 1: Check if predefined info exists
        print("\n1️⃣ Checking predefined info in database...")
        admission_info = PredefinedInfo.query.filter_by(section='admission', title='Admission Process').first()
        if admission_info:
            print(f"✅ Found admission info: {admission_info.title}")
        else:
            print("❌ No admission info found in database")
            return False
        
        # Test 2: Test bot fetching from database
        print("\n2️⃣ Testing bot response from database...")
        response = bot_service._admission_info("test_phone")
        if "ADMISSION PROCESS" in response:
            print("✅ Bot successfully fetched admission info from database")
        else:
            print("❌ Bot not fetching from database correctly")
            print(f"Response: {response[:100]}...")
            return False
        
        # Test 3: Test real-time update
        print("\n3️⃣ Testing real-time update capability...")
        
        # Store original content
        original_content = admission_info.content
        
        # Update content
        test_content = """📚 **UPDATED ADMISSION PROCESS**

🔴 **THIS IS A TEST UPDATE**
📋 **Eligibility Criteria:**
• Minimum 75% in 10+2 for UG courses (UPDATED)
• Valid score in entrance exam (JEE/CET/etc.)
• Age limit: As per university norms

📝 **Application Process:**
1. Fill online application form
2. Upload required documents
3. Pay application fee (₹750) - UPDATED
4. Appear for counseling/interview
5. Document verification
6. Fee payment and admission confirmation

📞 **Updated Contact:**
Admission Cell: +91-99999-99999
Email: updated-admission@college.edu

Issued by: Admission Department - UPDATED"""
        
        admission_info.content = test_content
        db.session.commit()
        
        # Test bot response after update
        updated_response = bot_service._admission_info("test_phone")
        if "UPDATED" in updated_response and "75%" in updated_response:
            print("✅ Bot successfully fetched updated content in real-time!")
        else:
            print("❌ Bot not fetching updated content")
            print(f"Updated response: {updated_response[:100]}...")
            # Restore original content
            admission_info.content = original_content
            db.session.commit()
            return False
        
        # Restore original content
        admission_info.content = original_content
        db.session.commit()
        
        # Test 4: Test other sections
        print("\n4️⃣ Testing other sections...")
        
        sections_to_test = [
            ('courses', 'Courses & Fee Structure', '_course_info'),
            ('fees', 'General Fee Structure', '_fee_structure'),
            ('facilities', 'College Facilities', '_facilities_info'),
            ('contact', 'College Contact Information', '_contact_info')
        ]
        
        all_passed = True
        for section, title, method_name in sections_to_test:
            info = PredefinedInfo.query.filter_by(section=section, title=title).first()
            if info:
                method = getattr(bot_service, method_name)
                response = method("test_phone")
                if response and len(response) > 50:
                    print(f"✅ {section.title()}: Bot successfully fetched from database")
                else:
                    print(f"❌ {section.title()}: Bot response issue")
                    all_passed = False
            else:
                print(f"❌ {section.title()}: No info found in database")
                all_passed = False
        
        if all_passed:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Bot is now fetching information from predefined info database")
            print("✅ Real-time updates are working correctly")
            print("✅ Admin can now update information and it will reflect immediately")
        else:
            print("\n❌ Some tests failed")
            return False
        
        return True

def test_fallback_mechanism():
    """Test that bot falls back to static content when no predefined info exists"""
    app = create_app()
    
    with app.app_context():
        print("\n🛡️ Testing Fallback Mechanism")
        print("=" * 50)
        
        bot_service = ChatbotService()
        
        # Temporarily deactivate all admission info
        admission_infos = PredefinedInfo.query.filter_by(section='admission').all()
        original_active_states = []
        
        for info in admission_infos:
            original_active_states.append(info.is_active)
            info.is_active = False
        
        db.session.commit()
        
        # Test fallback
        response = bot_service._admission_info("test_phone")
        if "ADMISSION PROCESS" in response and "Minimum 60%" in response:
            print("✅ Fallback to static content works correctly")
        else:
            print("❌ Fallback mechanism not working")
            return False
        
        # Restore original states
        for i, info in enumerate(admission_infos):
            info.is_active = original_active_states[i]
        
        db.session.commit()
        
        return True

if __name__ == '__main__':
    print("🚀 Starting Predefined Info Integration Tests")
    print("=" * 60)
    
    success = test_predefined_info_integration()
    if success:
        success = test_fallback_mechanism()
    
    if success:
        print("\n🎊 ALL INTEGRATION TESTS COMPLETED SUCCESSFULLY!")
        print("\n📋 Summary:")
        print("• Bot now fetches information from PredefinedInfo database")
        print("• Real-time updates are working")
        print("• Fallback mechanism is functional")
        print("• Admin can manage content through dashboard")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        sys.exit(1)
