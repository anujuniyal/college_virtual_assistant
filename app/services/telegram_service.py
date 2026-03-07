"""
Telegram Bot Service for EduBot
"""
import requests
import logging
from flask import current_app
from app.chatbot.service import ChatbotService

# Set up logger
logger = logging.getLogger(__name__)

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
        """Map Telegram user ID to actual phone number"""
        try:
            # Proper phone mapping - use phone numbers as keys
            # This maps Telegram user IDs to the actual phone numbers in the student database
            phone_mapping = {
                '7229077719': '9760387360',  # Your Telegram ID -> Anuj Uniyal's phone
                '123456789': '9760387360',  # Test user for bot testing
                # Add more mappings as needed for actual users
                # Format: 'telegram_user_id': 'student_phone_number_from_database'
            }
            
            telegram_user_id_str = str(telegram_user_id)
            actual_phone = phone_mapping.get(telegram_user_id_str)
            
            if actual_phone:
                logger.info(f"Mapped Telegram user {telegram_user_id_str} to phone {actual_phone}")
                return f"whatsapp:+{actual_phone}"
            logger.warning(f"No phone mapping found for Telegram user {telegram_user_id_str}")
            return None
                
        except Exception as e:
            logger.error(f"Error in phone number mapping: {str(e)}")
            return None
    
    def process_update(self, update):
        """Process incoming Telegram update"""
        try:
            if not update or not isinstance(update, dict):
                logger.error("Invalid update received")
                return None
                
            message = update.get('message', {})
            if not message or not isinstance(message, dict):
                logger.error("Invalid message in update")
                return None
                
            chat_id = message.get('chat', {}).get('id')
            text = message.get('text', '').strip()
            
            if not text or not chat_id:
                logger.warning("Empty message or missing chat ID")
                return None
            
            # Validate chat_id
            if not isinstance(chat_id, int) or chat_id <= 0:
                logger.error(f"Invalid chat_id: {chat_id}")
                return None
            
            # Get user info for phone number mapping
            user = message.get('from', {})
            if not user or not isinstance(user, dict):
                logger.error("Invalid user info in message")
                return None
                
            telegram_user_id = str(user.get('id', ''))
            if not telegram_user_id:
                logger.error("Missing user ID")
                return None
            
            # Map Telegram user ID to actual phone number
            phone_number = self._get_phone_number_from_mapping(telegram_user_id)
            logger.info(f"Mapped phone number for user {telegram_user_id}: {phone_number}")

            is_mapped_user = bool(phone_number)

            if not is_mapped_user:
                if text.lower().startswith('register') or text.lower().startswith('verify'):
                    # Extract roll number from registration message
                    import re
                    roll_match = re.search(r'register\s+([A-Z0-9]+)', text, re.IGNORECASE)
                    if roll_match:
                        roll_number = roll_match.group(1).upper()
                        response = f"✅ **Registration Request Received!**\n\n📚 Roll Number: {roll_number}\n\n🔄 Your registration is being processed.\n\n📋 Available Services (after registration):\n• View Results\n• Check Notices\n• Fee Status\n• Faculty Info\n• File Complaint\n\n⏳ Please wait for admin approval.\n\n🔔 You'll receive a confirmation once approved."
                    else:
                        response = (
                            "❌ **Registration Failed!**\n\n"
                            "Please use format: `register ROLL_NUMBER`\n\n"
                            f"Example: `register EDU20240051`\n\n"
                            "Need help? Type: `help`"
                        )
                    return self.send_message(chat_id, response)
                else:
                    # Provide visitor services
                    response = (
                        "👋 **Welcome to EduBot!**\n\n"
                        "📖 **Available Services:**\n\n"
                        "📚 `admission` - Admission info\n"
                        "📖 `courses` - Course details\n"
                        "💰 `fees` - Fee structure\n"
                        "🏫 `facilities` - Campus info\n"
                        "👨‍🏫 `faculty` - Faculty directory\n"
                        "ℹ️ `help` - Show this menu\n\n"
                        "🎓 **Students:** Register with `register ROLL_NUMBER`\n\n"
                        f"📞 **Need Help?** Contact admin\n\n"
                        f"🤖 **Bot Status:** Active"
                    )
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

            if not is_mapped_user and response:
                response = (
                    "Visitor mode: you can use admission/course/fees/facilities/faculty/help. "
                    f"To unlock student services, share your Telegram ID with admin: {telegram_user_id}.\n\n"
                    + response
                )
            
            # Send response back to Telegram
            return self.send_message(chat_id, response)
            
        except Exception as e:
            logger.error(f"Error processing Telegram update: {str(e)}")
            return None
    
    def send_message(self, chat_id, text):
        """Send message to Telegram chat"""
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
            
            logger.info(f"Sending message to chat_id {chat_id}: {text[:100]}...")
            response = requests.post(url, json=data, timeout=10)
            
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
                    return False
            else:
                logger.error(f"HTTP error sending message: {response.status_code}")
                logger.error(f"Response body: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("Timeout while sending message to Telegram")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error sending message: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
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
