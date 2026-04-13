"""
Email Service - Resend API for Render, SMTP fallback for local
"""
from flask import current_app
from app.config import Config
import os


class EmailService:
    """Email sending service with Resend API for Render and SMTP fallback"""
    
    @staticmethod
    def send_email(to: str, subject: str, body: str, html: str = None, attachments: list = None) -> bool:
        """
        Send email using Resend API (Render) or SMTP (local)
        Returns: True if successful, False otherwise
        """
        try:
            # Import Resend service
            from app.services.resend_email_service import EmailService as ResendEmailService
            
            # Use Resend API service which handles Render vs local automatically
            return ResendEmailService.send_email(to, subject, body, html, attachments)
            
        except Exception as e:
            current_app.logger.error(f"Email service error: {str(e)}")
            return False
    
    @staticmethod
    def send_weekly_report(admin_email: str, report_data: dict, csv_file_path: str = None) -> bool:
        """Send weekly analytics report to admin with CSV attachment"""
        try:
            # Import Resend service
            from app.services.resend_email_service import EmailService as ResendEmailService
            
            # Use Resend API service which handles Render vs local automatically
            return ResendEmailService.send_weekly_report(admin_email, report_data, csv_file_path)
                
        except Exception as e:
            current_app.logger.error(f"Weekly report email service error: {str(e)}")
            return False
