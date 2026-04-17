#!/usr/bin/env python3
"""
Script to add debug logging to Telegram verification process
"""

def add_telegram_debug():
    """Add debug logging to track Telegram ID updates"""
    
    with open('app/chatbot/service.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add debug logging before and after linking Telegram account
    old_link_code = """        # Link Telegram account to student record if this is a Telegram user
        if telegram_phone.startswith('whatsapp:+visitor_'):
            # Extract Telegram user ID from visitor phone number
            telegram_user_id = telegram_phone.replace('whatsapp:+visitor_', '')
            try:
                success, message = student.link_telegram_account(telegram_user_id)
                if success:
                    current_app.logger.info(f"Successfully linked Telegram account for student {student.name} ({student.roll_number})")
                else:
                    current_app.logger.warning(f"Failed to link Telegram account: {message}")
            except Exception as e:
                current_app.logger.error(f"Error linking Telegram account: {str(e)}")"""
    
    new_link_code = """        # Link Telegram account to student record if this is a Telegram user
        if telegram_phone.startswith('whatsapp:+visitor_'):
            # Extract Telegram user ID from visitor phone number
            telegram_user_id = telegram_phone.replace('whatsapp:+visitor_', '')
            try:
                current_app.logger.info(f"About to link Telegram account - Student: {student.name}, Telegram ID: {telegram_user_id}")
                current_app.logger.info(f"Student current telegram_user_id: {student.telegram_user_id}")
                current_app.logger.info(f"Student current telegram_verified: {student.telegram_verified}")
                success, message = student.link_telegram_account(telegram_user_id)
                current_app.logger.info(f"link_telegram_account returned: success={success}, message={message}")
                if success:
                    current_app.logger.info(f"Successfully linked Telegram account for student {student.name} ({student.roll_number})")
                    current_app.logger.info(f"Student telegram_user_id after linking: {student.telegram_user_id}")
                    current_app.logger.info(f"Student telegram_verified after linking: {student.telegram_verified}")
                else:
                    current_app.logger.warning(f"Failed to link Telegram account: {message}")
            except Exception as e:
                current_app.logger.error(f"Error linking Telegram account: {str(e)}")"""
    
    content = content.replace(old_link_code, new_link_code)
    
    with open('app/chatbot/service.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Telegram debug logging added successfully!")

if __name__ == "__main__":
    add_telegram_debug()
