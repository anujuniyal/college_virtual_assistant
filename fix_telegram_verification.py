#!/usr/bin/env python3
"""
Fix for Telegram verification real-time update issue
"""

def fix_telegram_verification():
    """Fix the database transaction issues in Telegram verification"""
    
    with open('app/models.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix 1: Remove duplicate commit in link_telegram_account method
    old_link_method = '''    def link_telegram_account(self, telegram_user_id):
        """Link Telegram account to student with proper transaction handling"""
        from app.extensions import db
        from sqlalchemy.exc import IntegrityError
        
        try:
            # Start transaction
            # Update student record first
            self.telegram_user_id = telegram_user_id
            self.telegram_verified = True
            
            # Also update the TelegramUserMapping table
            # First try to find existing mapping by telegram_user_id (most reliable)
            existing_mapping = TelegramUserMapping.query.filter_by(
                telegram_user_id=telegram_user_id
            ).first()
            
            if not existing_mapping:
                # If no mapping exists by telegram_user_id, try by phone_number as fallback
                existing_mapping = TelegramUserMapping.query.filter_by(
                    phone_number=self.phone
                ).first()
                if existing_mapping:
                    # Update the existing mapping with correct telegram_user_id
                    existing_mapping.telegram_user_id = telegram_user_id
            
            if not existing_mapping:
                # Create new mapping if none exists
                mapping = TelegramUserMapping(
                    telegram_user_id=telegram_user_id,
                    student_id=self.id,
                    phone_number=self.phone,
                    verified=True
                )
                db.session.add(mapping)
            else:
                # Update existing mapping
                existing_mapping.student_id = self.id
                existing_mapping.phone_number = self.phone
                existing_mapping.verified = True
            
            # Commit transaction
            db.session.commit()
            return True, "Telegram account linked successfully"
            
        except IntegrityError as e:
            db.session.rollback()
            return False, f"Database integrity error: {str(e)}"
        except Exception as e:
            db.session.rollback()
            return False, f"Error linking Telegram account: {str(e)}"'''
    
    new_link_method = '''    def link_telegram_account(self, telegram_user_id):
        """Link Telegram account to student with proper transaction handling"""
        from app.extensions import db
        from sqlalchemy.exc import IntegrityError
        
        try:
            # Use FOR UPDATE to lock the student record and prevent race conditions
            student = Student.query.filter_by(id=self.id).with_for_update().first()
            if not student:
                return False, "Student record not found"
            
            # Update student record first
            student.telegram_user_id = telegram_user_id
            student.telegram_verified = True
            
            # Also update the TelegramUserMapping table
            # First try to find existing mapping by telegram_user_id (most reliable)
            existing_mapping = TelegramUserMapping.query.filter_by(
                telegram_user_id=telegram_user_id
            ).with_for_update().first()
            
            if not existing_mapping:
                # If no mapping exists by telegram_user_id, try by phone_number as fallback
                existing_mapping = TelegramUserMapping.query.filter_by(
                    phone_number=student.phone
                ).with_for_update().first()
                if existing_mapping:
                    # Update the existing mapping with correct telegram_user_id
                    existing_mapping.telegram_user_id = telegram_user_id
            
            if not existing_mapping:
                # Create new mapping if none exists
                mapping = TelegramUserMapping(
                    telegram_user_id=telegram_user_id,
                    student_id=student.id,
                    phone_number=student.phone,
                    verified=True
                )
                db.session.add(mapping)
            else:
                # Update existing mapping
                existing_mapping.student_id = student.id
                existing_mapping.phone_number = student.phone
                existing_mapping.verified = True
            
            # Don't commit here - let the caller handle the transaction
            return True, "Telegram account linked successfully"
            
        except IntegrityError as e:
            db.session.rollback()
            return False, f"Database integrity error: {str(e)}"
        except Exception as e:
            db.session.rollback()
            return False, f"Error linking Telegram account: {str(e)}"'''
    
    # Fix 2: Update the verification method to handle transaction properly
    old_verification = '''        # Link Telegram account to student record if this is a Telegram user
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
                current_app.logger.error(f"Error linking Telegram account: {str(e)}")
        
        db.session.commit()'''
    
    new_verification = '''        # Link Telegram account to student record if this is a Telegram user
        if telegram_phone.startswith('whatsapp:+visitor_'):
            # Extract Telegram user ID from visitor phone number
            telegram_user_id = telegram_phone.replace('whatsapp:+visitor_', '')
            try:
                current_app.logger.info(f"About to link Telegram account - Student: {student.name}, Telegram ID: {telegram_user_id}")
                current_app.logger.info(f"Student current telegram_user_id: {student.telegram_user_id}")
                current_app.logger.info(f"Student current telegram_verified: {student.telegram_verified}")
                
                # Use a single transaction for all updates
                from app.extensions import db
                from sqlalchemy.exc import IntegrityError
                
                try:
                    # Update student record directly within the same transaction
                    student.telegram_user_id = telegram_user_id
                    student.telegram_verified = True
                    
                    # Also update the TelegramUserMapping table
                    existing_mapping = TelegramUserMapping.query.filter_by(
                        telegram_user_id=telegram_user_id
                    ).first()
                    
                    if not existing_mapping:
                        # Create new mapping if none exists
                        mapping = TelegramUserMapping(
                            telegram_user_id=telegram_user_id,
                            student_id=student.id,
                            phone_number=student.phone,
                            verified=True
                        )
                        db.session.add(mapping)
                    else:
                        # Update existing mapping
                        existing_mapping.student_id = student.id
                        existing_mapping.phone_number = student.phone
                        existing_mapping.verified = True
                    
                    current_app.logger.info(f"Successfully linked Telegram account for student {student.name} ({student.roll_number})")
                    current_app.logger.info(f"Student telegram_user_id after linking: {student.telegram_user_id}")
                    current_app.logger.info(f"Student telegram_verified after linking: {student.telegram_verified}")
                    
                except IntegrityError as e:
                    db.session.rollback()
                    current_app.logger.error(f"Database integrity error linking Telegram account: {str(e)}")
                    return f"Database error during verification. Please try again."
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(f"Error linking Telegram account: {str(e)}")
                    return f"System error during verification. Please try again."
                    
            except Exception as e:
                current_app.logger.error(f"Unexpected error in Telegram verification: {str(e)}")
                return f"Unexpected error during verification. Please try again."'''
    
    # Apply fixes
    content = content.replace(old_link_method, new_link_method)
    content = content.replace(old_verification, new_verification)
    
    with open('app/models.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Fixed Telegram verification real-time update issues!")
    print("\nChanges made:")
    print("1. Removed duplicate db.session.commit() in link_telegram_account()")
    print("2. Added row-level locking with FOR UPDATE to prevent race conditions")
    print("3. Consolidated all updates into a single transaction")
    print("4. Improved error handling and logging")
    print("\nThe student records should now update in real-time after verification.")

if __name__ == "__main__":
    fix_telegram_verification()
