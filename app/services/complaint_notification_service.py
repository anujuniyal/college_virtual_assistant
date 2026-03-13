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
