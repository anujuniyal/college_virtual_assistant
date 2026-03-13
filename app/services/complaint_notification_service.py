"""
Complaint Notification Service
"""
from datetime import datetime
from flask import current_app
from app.extensions import db
from app.models import Admin, Complaint, Student, Notification


class ComplaintNotificationService:
    """Service to handle complaint notifications to admin/HOD"""
    
    @staticmethod
    def notify_admin_hod(complaint_id: int, category: str, description: str, student_name: str, roll_number: str):
        """Send notification to all admin users when a complaint is received"""
        try:
            # Get all admin users
            admin_users = Admin.query.filter_by(role='admin').all()
            
            if not admin_users:
                current_app.logger.warning("No admin users found to notify about complaint")
                return False
            
            # Create notification title and content
            title = f"🚨 New {category.upper()} Complaint Filed"
            
            content = f"""📋 **Complaint Details:**

🆔 **Complaint ID:** {complaint_id}
👤 **Student:** {student_name} ({roll_number})
🏷️ **Category:** {category.upper()}
📝 **Description:** {description}

⏰ **Time:** {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}

🔍 **Action Required:** Please review and take appropriate action.

---
*This is an automated notification from the College Virtual Assistant System*"""
            
            # Create notification record for each admin
            for admin in admin_users:
                notification = Notification(
                    title=title,
                    content=content,
                    notification_type='complaint',
                    priority='high',
                    expires_at=datetime.utcnow().replace(hour=23, minute=59, second=59),  # Expires today
                    created_by=admin.id  # Self-created notification
                )
                db.session.add(notification)
            
            # Commit all notifications
            db.session.commit()
            
            current_app.logger.info(f"Complaint notification sent to {len(admin_users)} admin users for complaint ID: {complaint_id}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error sending complaint notification: {str(e)}")
            db.session.rollback()
            return False
    
    @staticmethod
    def notify_complaint_status_update(complaint_id: int, old_status: str, new_status: str, student_name: str):
        """Send notification when complaint status is updated"""
        try:
            # Get all admin users
            admin_users = Admin.query.filter_by(role='admin').all()
            
            if not admin_users:
                return False
            
            # Create notification for status update
            title = f"📝 Complaint Status Updated"
            
            content = f"""📋 **Status Update:**

🆔 **Complaint ID:** {complaint_id}
👤 **Student:** {student_name}
📊 **Status Change:** {old_status.upper()} → {new_status.upper()}

⏰ **Updated:** {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}

---
*Complaint status has been updated in the system*"""
            
            # Create notification record for each admin
            for admin in admin_users:
                notification = Notification(
                    title=title,
                    content=content,
                    notification_type='complaint_update',
                    priority='medium',
                    expires_at=datetime.utcnow().replace(hour=23, minute=59, second=59),  # Expires today
                    created_by=admin.id  # Self-created notification
                )
                db.session.add(notification)
            
            # Commit all notifications
            db.session.commit()
            
            current_app.logger.info(f"Complaint status update notification sent for complaint ID: {complaint_id}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error sending status update notification: {str(e)}")
            db.session.rollback()
            return False
    
    @staticmethod
    def notify_student_telegram(complaint_id: int, old_status: str, new_status: str, student_id: int, complaint_details=None):
        """Send Telegram notification to student when complaint status is updated"""
        try:
            # Get student information
            student = Student.query.get(student_id)
            if not student:
                current_app.logger.warning(f"Student not found for complaint ID: {complaint_id}")
                return False
            
            # Check if student has verified Telegram account
            if not student.is_telegram_verified():
                current_app.logger.info(f"Student {student.roll_number} does not have verified Telegram account")
                return False
            
            # Get complaint details (either from provided details or from database)
            if complaint_details:
                complaint_category = complaint_details.get('category', 'Unknown')
                complaint_description = complaint_details.get('description', 'No description available')
            else:
                complaint = Complaint.query.get(complaint_id)
                if not complaint:
                    current_app.logger.warning(f"Complaint not found: {complaint_id}")
                    return False
                complaint_category = complaint.category
                complaint_description = complaint.description
            
            # Create notification message for student
            status_emoji = {
                'pending': '⏳',
                'investigating': '🔍', 
                'resolved': '✅',
                'deleted': '🗑️'
            }
            
            emoji = status_emoji.get(new_status.lower(), '📋')
            
            # Handle deleted complaints differently
            if new_status.lower() == 'deleted':
                message = f"""{emoji} **Complaint Deleted**

🆔 **Complaint ID:** {complaint_id}
🏷️ **Category:** {complaint_category.title()}

👋 **Hello {student.name},**
Your complaint has been deleted from the system.

📅 **Deleted on:** {datetime.now().strftime('%d-%m-%Y at %I:%M %p')}

📝 **Note:** If you have questions about this action, please contact the administration.

---
*College Virtual Assistant System*
*This is an automated notification. Please do not reply to this message.*"""
            else:
                message = f"""{emoji} **Complaint Status Update**

🆔 **Complaint ID:** {complaint_id}
🏷️ **Category:** {complaint_category.title()}
📊 **Status Change:** {old_status.upper()} → {new_status.upper()}

👋 **Hello {student.name},**
Your complaint status has been updated.

📅 **Updated on:** {datetime.now().strftime('%d-%m-%Y at %I:%M %p')}

🔗 **Track Status:** You can check your complaint status anytime on the student portal.

---
*College Virtual Assistant System*
*This is an automated notification. Please do not reply to this message.*"""
            
            # Initialize Telegram service
            from app.services.telegram_service import TelegramBotService
            telegram_service = TelegramBotService()
            bot_token = current_app.config.get('TELEGRAM_BOT_TOKEN')
            
            if not bot_token:
                current_app.logger.error("Telegram bot token not configured")
                return False
            
            telegram_service.bot_token = bot_token
            
            # Send message to student's Telegram
            chat_id = int(student.telegram_user_id)
            success = telegram_service.send_message(chat_id, message)
            
            if success:
                current_app.logger.info(f"Telegram notification sent to student {student.roll_number} for complaint ID: {complaint_id}")
                return True
            else:
                current_app.logger.error(f"Failed to send Telegram notification to student {student.roll_number}")
                return False
            
        except ValueError as e:
            current_app.logger.error(f"Invalid Telegram user ID for student {student_id if 'student_id' in locals() else 'unknown'}: {str(e)}")
            return False
        except Exception as e:
            current_app.logger.error(f"Error sending Telegram notification to student: {str(e)}")
            return False
