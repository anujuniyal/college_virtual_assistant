"""
Telegram Bot Service for EduBot
"""
import requests
import logging
import re
from flask import current_app
from app.chatbot.service import ChatbotService
from app.models import TelegramUserMapping, Student, Session
from app.extensions import db

# Set up logger
logger = logging.getLogger(__name__)

# Input validation patterns
TELEGRAM_USER_ID_PATTERN = re.compile(r'^[0-9]{1,20}$')
PHONE_PATTERN = re.compile(r'^[0-9]{10,15}$')
SAFE_TEXT_PATTERN = re.compile(r'^[\w\s\-\.\,\?\!\@\#\$\%\&\*\(\)\[\]\{\}\:\;\"\'\/\\\|\=\+\`\~\<\>]*$', re.UNICODE)

def validate_telegram_user_id(user_id):
    """Validate Telegram user ID"""
    if not user_id:
        return False, "User ID is required"
    
    user_id_str = str(user_id).strip()
    if not TELEGRAM_USER_ID_PATTERN.match(user_id_str):
        return False, "Invalid user ID format"
    
    # Convert to integer and check range
    try:
        user_id_int = int(user_id_str)
        if user_id_int <= 0 or user_id_int > 9223372036854775807:  # Max 64-bit integer
            return False, "User ID out of valid range"
    except ValueError:
        return False, "Invalid user ID"
    
    return True, user_id_str

def validate_phone_number(phone):
    """Validate phone number"""
    if not phone:
        return False, "Phone number is required"
    
    # Extract digits only
    digits = re.sub(r'[^\d]', '', str(phone))
    if not digits:
        return False, "Invalid phone number"
    
    # Check length (10-15 digits for international numbers)
    if len(digits) < 10 or len(digits) > 15:
        return False, "Phone number must be 10-15 digits"
    
    return True, digits

def validate_message_text(text):
    """Validate and sanitize message text"""
    if not text:
        return False, "Message text is required"
    
    if not isinstance(text, str):
        return False, "Message must be a string"
    
    # Length validation
    if len(text) > 4096:  # Telegram limit
        return False, "Message too long (max 4096 characters)"
    
    # Basic sanitization - remove potentially harmful characters
    sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    return True, sanitized

class TelegramBotService:
    """Telegram Bot Service"""
    
    def __init__(self):
        self.bot_token = None
        self.webhook_url = None
        self.chatbot_service = ChatbotService()
    
    def initialize(self, bot_token, webhook_url):
        """Initialize Telegram bot"""
        self.bot_token = bot_token
        self.webhook_url = webhook_url
        return self.set_webhook()
    
    def set_webhook(self):
        """Set webhook for Telegram bot"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/setWebhook"
            data = {
                'url': self.webhook_url,
                'allowed_updates': ['message']
            }
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    logger.info("Telegram webhook set successfully")
                    return True
                else:
                    logger.error(f"Failed to set webhook: {result.get('description', 'Unknown error')}")
                    return False
            else:
                logger.error(f"HTTP error setting webhook: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error setting Telegram webhook: {str(e)}")
            return False
    
    def _get_phone_number_from_mapping(self, telegram_user_id):
        """
        Get phone number for Telegram user ID.

        Note: this returns the phone once the user has shared it and it was found
        in Student records. Full student access still requires roll verification,
        which is tracked via Session. After roll verification succeeds, we mark
        the mapping as verified for convenience.
        """
        try:
            telegram_user_id_str = str(telegram_user_id)
            mapping = TelegramUserMapping.query.filter_by(telegram_user_id=telegram_user_id_str).first()
            if not mapping:
                logger.warning(f"No Telegram mapping found for user {telegram_user_id_str}")
                return None

            # Extra safety: ensure mapped phone still exists in student records.
            student = Student.query.get(mapping.student_id)
            if not student or student.phone != mapping.phone_number:
                logger.warning(f"Stale Telegram mapping for user {telegram_user_id_str}")
                return None

            logger.info(f"Mapped Telegram user {telegram_user_id_str} to phone {mapping.phone_number}")
            return f"whatsapp:+{mapping.phone_number}"
                
        except Exception as e:
            logger.error(f"Error in phone number mapping: {str(e)}")
            return None

    def _normalize_phone(self, raw: str):
        """Normalize phone number with validation"""
        if not raw:
            return None
        
        # Validate phone number format
        is_valid, phone = validate_phone_number(raw)
        if not is_valid:
            logger.warning(f"Invalid phone number format: {raw}")
            return None
        
        return phone

    def _build_contact_request_markup(self):
        return {
            "keyboard": [[{"text": "Share phone number", "request_contact": True}]],
            "one_time_keyboard": True,
            "resize_keyboard": True,
        }

    def _verify_and_save_phone(self, telegram_user_id: str, phone_raw: str) -> bool:
        """Verify that phone exists in Student records, then save mapping for this Telegram user."""
        phone = self._normalize_phone(phone_raw)
        if not phone:
            return False

        try:
            # Use database transaction to prevent race conditions
            from app.extensions import db
            from sqlalchemy.exc import IntegrityError
            
            # Check if student exists with multiple phone format attempts
            student = None
            
            # First try with the exact normalized phone
            student = Student.query.filter_by(phone=phone).first()
            
            # If not found and phone has country code, try without it
            if not student and len(phone) == 12 and phone.startswith('91'):
                # Remove '91' country code for Indian numbers
                phone_without_country = phone[2:]
                student = Student.query.filter_by(phone=phone_without_country).first()
                if student:
                    phone = phone_without_country  # Update to use database format
                    logger.info(f"Phone matched after removing country code: {phone}")
            
            # If still not found and phone is 10 digits with leading zero, try without zero
            if not student and len(phone) == 11 and phone.startswith('0'):
                phone_without_zero = phone[1:]
                student = Student.query.filter_by(phone=phone_without_zero).first()
                if student:
                    phone = phone_without_zero  # Update to use database format
                    logger.info(f"Phone matched after removing leading zero: {phone}")
            
            # If still not found and phone is 10 digits, try with Indian country code
            if not student and len(phone) == 10:
                phone_with_country = '91' + phone
                student = Student.query.filter_by(phone=phone_with_country).first()
                if student:
                    phone = phone_with_country  # Update to use database format
                    logger.info(f"Phone matched after adding Indian country code: {phone}")
            
            if not student:
                # Log the failed attempt for debugging
                logger.warning(f"Phone verification failed - Phone {phone} not found in student records")
                return False

            logger.info(f"Phone verification successful - Found student: {student.name} ({student.roll_number})")

            # Use FOR UPDATE to lock the row and prevent race conditions
            mapping = TelegramUserMapping.query.filter_by(telegram_user_id=str(telegram_user_id)).with_for_update().first()
            
            if not mapping:
                # Create new mapping with proper error handling
                mapping = TelegramUserMapping(
                    telegram_user_id=str(telegram_user_id),
                    student_id=student.id,
                    phone_number=phone,
                    verified=False,
                )
                db.session.add(mapping)
            else:
                # Update existing mapping
                mapping.student_id = student.id
                mapping.phone_number=phone
                # Student verification happens after roll verification, not here.
                mapping.verified = False

            db.session.commit()
            logger.info(f"Successfully saved/updated phone mapping for Telegram user {telegram_user_id} -> Student {student.name}")
            return True
            
        except IntegrityError as e:
            db.session.rollback()
            logger.warning(f"Integrity error saving phone mapping for {telegram_user_id}: {str(e)}")
            # Race condition - another process created the mapping
            # Try to fetch the existing mapping
            try:
                existing_mapping = TelegramUserMapping.query.filter_by(telegram_user_id=str(telegram_user_id)).first()
                if existing_mapping and existing_mapping.phone_number == phone:
                    return True
            except Exception:
                pass
            return False
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving phone mapping for {telegram_user_id}: {str(e)}")
            return False
    
    def process_update(self, update):
        """Process incoming Telegram update with proper validation"""
        try:
            # Validate update structure
            if not update or not isinstance(update, dict):
                logger.error("Invalid update received: not a dictionary")
                return None
                
            message = update.get('message', {})
            if not message or not isinstance(message, dict):
                logger.error("Invalid message in update: not a dictionary")
                return None
                
            # Extract and validate chat_id
            chat_info = message.get('chat', {})
            if not isinstance(chat_info, dict):
                logger.error("Invalid chat info in message")
                return None
                
            chat_id = chat_info.get('id')
            is_valid_chat_id, validated_chat_id = validate_telegram_user_id(chat_id)
            if not is_valid_chat_id:
                logger.error(f"Invalid chat_id: {chat_id}")
                return None
            
            chat_id = int(validated_chat_id)
            
            # Extract and validate text
            text = message.get('text', '').strip()
            if text:
                is_valid_text, sanitized_text = validate_message_text(text)
                if not is_valid_text:
                    logger.error(f"Invalid message text: {text[:100]}...")
                    return None
                text = sanitized_text

            # Handle contact share with validation
            contact = message.get('contact')
            if isinstance(contact, dict) and chat_id:
                user_info = message.get('from', {})
                if not isinstance(user_info, dict):
                    logger.error("Invalid user info in contact message")
                    return None
                
                sender_id = user_info.get('id')
                is_valid_sender, validated_sender = validate_telegram_user_id(sender_id)
                if not is_valid_sender:
                    logger.error("Invalid sender ID in contact message")
                    return None
                
                contact_user_id = contact.get('user_id')
                is_valid_contact, validated_contact = validate_telegram_user_id(contact_user_id)
                if not is_valid_contact or validated_contact != validated_sender:
                    return self.send_message(chat_id, "❌ Please share *your own* phone number using the button.")

                phone_raw = contact.get('phone_number', '')
                ok = self._verify_and_save_phone(validated_sender, phone_raw)
                if ok:
                    return self.send_message(
                        chat_id,
                        "✅ Phone number matched with our student records.\n\n"
                        "🎓 **Student Verification Step 2 Complete**\n\n"
                        "Now enter your roll number to complete verification:\n\n"
                        "Type: `register YOUR_ROLL_NUMBER`\n"
                        "Example: `register EDU20240051`\n\n"
                        "📝 Note: Roll number must match the phone number in our records.",
                    )
                return self.send_message(
                    chat_id,
                    "❌ This phone number is not found in our student records.\n\nPlease contact admin to update your registered phone number.",
                )
            
            if not text or not chat_id:
                logger.warning("Empty message or missing chat ID")
                return None
            
            # Get and validate user info
            user = message.get('from', {})
            if not user or not isinstance(user, dict):
                logger.error("Invalid user info in message")
                return None
                
            telegram_user_id = user.get('id', '')
            is_valid_user, validated_user_id = validate_telegram_user_id(telegram_user_id)
            if not is_valid_user:
                logger.error("Missing or invalid user ID")
                return None
            
            # Map Telegram user ID to actual phone number
            phone_number = self._get_phone_number_from_mapping(validated_user_id)
            logger.info(f"Mapped phone number for user {validated_user_id}: {phone_number}")

            is_mapped_user = bool(phone_number)

            if not is_mapped_user:
                if text.lower().startswith('register') or text.lower().startswith('verify'):
                    return self.send_message(
                        chat_id,
                        "🎓 **Student Verification Required**\n\nTo access student services, please share your phone number (must match student records).\n\n📱 Click the button below to share your phone number:",
                        reply_markup=self._build_contact_request_markup(),
                    )

                # For unmapped users, process visitor commands through chatbot service
                # Use a temporary phone number for visitor mode
                temp_phone = f"whatsapp:+visitor_{validated_user_id}"
                try:
                    response = self.chatbot_service.process_message(text, temp_phone)
                    logger.info(f"Chatbot response for visitor {validated_user_id}: {response}")
                    if not response:
                        logger.warning("Empty response from chatbot service for visitor")
                        response = "I'm sorry, I couldn't process your request. Please try again."
                except Exception as e:
                    logger.error(f"Error in chatbot service for visitor {validated_user_id}: {str(e)}")
                    response = "I'm experiencing technical difficulties. Please try again later."

                return self.send_message(chat_id, response)
            
            # Process message with chatbot service
            try:
                response = self.chatbot_service.process_message(text, phone_number)
                logger.info(f"Chatbot response: {response}")
                if not response:
                    logger.warning("Empty response from chatbot service")
                    response = "I'm sorry, I couldn't process your request. Please try again."
            except Exception as e:
                logger.error(f"Error in chatbot service: {str(e)}")
                response = "I'm experiencing technical difficulties. Please try again later."

            # If roll verification succeeded, ChatbotService will mark Session as verified.
            # When that happens, permanently link Telegram ID to student for convenience.
            try:
                session_obj = Session.query.filter_by(phone_number=phone_number).first()
                if session_obj and session_obj.verified and session_obj.student_id:
                    # Use proper transaction handling
                    from app.extensions import db
                    from sqlalchemy.exc import IntegrityError
                    
                    try:
                        # Get the student record
                        student = Student.query.get(session_obj.student_id)
                        if student:
                            # Use the student's link_telegram_account method to update both Student and TelegramUserMapping tables
                            success, message = student.link_telegram_account(str(validated_user_id))
                            if success:
                                logger.info(f"Successfully linked Telegram account for student {student.name} ({student.roll_number})")
                            else:
                                logger.warning(f"Failed to link Telegram account: {message}")
                        
                        # Also update the TelegramUserMapping table as backup
                        mapping = TelegramUserMapping.query.filter_by(telegram_user_id=str(validated_user_id)).with_for_update().first()
                        if mapping:
                            mapping.student_id = session_obj.student_id
                            mapping.phone_number = phone_number.replace('whatsapp:+', '')
                            mapping.verified = True
                        db.session.commit()
                        logger.info(f"Successfully finalized Telegram mapping for user {validated_user_id}")
                    except IntegrityError as e:
                        db.session.rollback()
                        logger.warning(f"Integrity error finalizing Telegram mapping: {str(e)}")
                    except Exception as e:
                        db.session.rollback()
                        logger.warning(f"Could not finalize Telegram mapping: {str(e)}")
            except Exception as e:
                logger.error(f"Database error in Telegram mapping finalization: {str(e)}")
            
            # Send response back to Telegram
            return self.send_message(chat_id, response)
            
        except Exception as e:
            logger.error(f"Error processing Telegram update: {str(e)}")
            return None
    
    def send_message(self, chat_id, text, reply_markup=None):
        """Send message to Telegram chat with comprehensive error handling"""
        try:
            # Validate inputs
            if not chat_id or not isinstance(chat_id, int) or chat_id <= 0:
                logger.error(f"Invalid chat_id for sending message: {chat_id}")
                return False
                
            if not text or not isinstance(text, str):
                logger.error("Invalid text for sending message")
                return False
            
            # Truncate message if too long (Telegram limit is 4096 characters)
            if len(text) > 4000:  # Leave some buffer
                text = text[:4000] + "...\n\n[Message truncated due to length]"
            
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'HTML'  # Enable HTML formatting
            }
            if reply_markup:
                data['reply_markup'] = reply_markup
            
            logger.info(f"Sending message to chat_id {chat_id}: {text[:100]}...")
            
            # Implement retry logic for network issues
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.post(url, json=data, timeout=10)
                    break
                except requests.exceptions.Timeout:
                    if attempt < max_retries - 1:
                        logger.warning(f"Timeout sending message (attempt {attempt + 1}), retrying...")
                        continue
                    else:
                        logger.error("Timeout while sending message to Telegram after all retries")
                        return False
                except requests.exceptions.ConnectionError:
                    if attempt < max_retries - 1:
                        logger.warning(f"Connection error sending message (attempt {attempt + 1}), retrying...")
                        continue
                    else:
                        logger.error("Connection error sending message to Telegram after all retries")
                        return False
            
            # Log full response for debugging
            logger.info(f"Telegram API response status: {response.status_code}")
            logger.info(f"Telegram API response body: {response.text[:500]}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    logger.info(f"Message sent successfully to chat_id: {chat_id}")
                    return True
                else:
                    error_desc = result.get('description', 'Unknown error')
                    error_code = result.get('error_code', 'Unknown')
                    logger.error(f"Telegram API error {error_code}: {error_desc}")
                    
                    # Handle specific error codes
                    if error_code == 429:
                        logger.warning("Rate limit exceeded, backing off...")
                        return False
                    elif error_code == 403:
                        logger.error("Bot was blocked by user")
                        return False
                    elif error_code == 400:
                        logger.error("Bad request - invalid parameters")
                        return False
                    
                    return False
            elif response.status_code == 429:
                logger.warning("Rate limit exceeded")
                retry_after = response.headers.get('retry-after', 5)
                logger.info(f"Will retry after {retry_after} seconds")
                return False
            elif response.status_code == 500:
                logger.error("Telegram server error")
                return False
            elif response.status_code == 403:
                logger.error("Forbidden - invalid bot token or blocked")
                return False
            else:
                logger.error(f"HTTP error sending message: {response.status_code}")
                logger.error(f"Response body: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("Timeout while sending message to Telegram")
            return False
        except requests.exceptions.ConnectionError:
            logger.error("Connection error sending message to Telegram")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error sending message: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending message: {str(e)}")
            return False
    
    def get_bot_info(self):
        """Get bot information"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    return result.get('result')
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting bot info: {str(e)}")
            return None
    
    def remove_webhook(self):
        """Remove webhook"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/deleteWebhook"
            response = requests.post(url, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('ok', False)
            
            return False
            
        except Exception as e:
            logger.error(f"Error removing webhook: {str(e)}")
            return False
