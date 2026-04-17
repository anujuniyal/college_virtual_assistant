#!/usr/bin/env python3
"""
Fix bot message to use 'register roll no.' format instead of just roll number
"""

def fix_bot_roll_message():
    """Update chatbot service to use 'register roll no.' format"""
    
    with open('app/chatbot/service.py', 'r', encoding='utf-8') as f:
        service_content = f.read()
    
    # Fix 1: Update the registration instruction message
    old_registration_message = '''        return "Please provide your roll number in format: EDU25001"'''
    
    new_registration_message = '''        return "Please provide your roll number in format: register EDU25001"'''
    
    service_content = service_content.replace(old_registration_message, new_registration_message)
    
    # Fix 2: Update the help message for registration
    old_help_registration = '''**Registration:**
1. Send your roll number (e.g., EDU25001)
2. Verify your phone number
3. Access student services'''
    
    new_help_registration = '''**Registration:**
1. Send your roll number (e.g., register EDU25001)
2. Verify your phone number
3. Access student services'''
    
    service_content = service_content.replace(old_help_registration, new_help_registration)
    
    # Fix 3: Update the logout message to show correct format
    old_logout_message = '''To access services again:
* Verify your roll number: EDU25001'''
    
    new_logout_message = '''To access services again:
* Verify your roll number: register EDU25001'''
    
    service_content = service_content.replace(old_logout_message, new_logout_message)
    
    # Fix 4: Update the visitor mode help message
    old_visitor_help = '''**Registration:**
Send your roll number (e.g., EDU25001) to verify and access student services'''
    
    new_visitor_help = '''**Registration:**
Send your roll number (e.g., register EDU25001) to verify and access student services'''
    
    service_content = service_content.replace(old_visitor_help, new_visitor_help)
    
    # Fix 5: Update the initial greeting message
    old_greeting = '''**Student Access:**
Send your roll number (e.g., EDU25001) to verify and access services'''
    
    new_greeting = '''**Student Access:**
Send your roll number (e.g., register EDU25001) to verify and access services'''
    
    service_content = service_content.replace(old_greeting, new_greeting)
    
    # Fix 6: Update the roll number verification instruction
    old_verification = '''        return "Please provide your roll number to verify your identity"'''
    
    new_verification = '''        return "Please provide your roll number in format: register EDU25001 to verify your identity"'''
    
    service_content = service_content.replace(old_verification, new_verification)
    
    with open('app/chatbot/service.py', 'w', encoding='utf-8') as f:
        f.write(service_content)
    
    print("Fixed bot roll number message format!")
    print("\nChanges made:")
    print("1. Updated registration instruction to use 'register EDU25001' format")
    print("2. Updated help messages to show correct format")
    print("3. Updated logout message to use correct format")
    print("4. Updated visitor mode help message")
    print("5. Updated initial greeting message")
    print("6. Updated verification instruction message")
    print("\nThe bot will now consistently ask for 'register roll no.' format!")

if __name__ == "__main__":
    fix_bot_roll_message()
