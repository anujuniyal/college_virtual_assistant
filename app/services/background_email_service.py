"""
Background Email Service - Works outside Flask application context
"""
import logging
import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional

# Set up logger for background operations
logger = logging.getLogger(__name__)


class BackgroundEmailService:
    """Email service that works in background threads without Flask context"""
    
    def __init__(self):
        # Get configuration from environment variables instead of Flask
        self.api_key = os.environ.get('RESEND_API_KEY')
        self.brevo_api_key = os.environ.get('BREVO_API_KEY')
        self.base_url = 'https://api.resend.com'
        self.brevo_base_url = 'https://api.brevo.com/v3'
        self.from_email = os.environ.get('MAIL_DEFAULT_SENDER', 'anujjaj007@gmail.com')
        self.mail_server = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
        self.mail_port = int(os.environ.get('MAIL_PORT', 587))
        self.mail_username = os.environ.get('MAIL_USERNAME', 'anujjaj007@gmail.com')
        self.mail_password = os.environ.get('MAIL_PASSWORD')
        self.is_render = os.environ.get('RENDER') == 'true' or os.environ.get('RENDER_SERVICE_ID') is not None
    
    def send_email(self, to: str, subject: str, body: str, html: Optional[str] = None, attachments: Optional[list] = None) -> bool:
        """
        Send email using available services in priority order:
        1. Brevo API (if available)
        2. Resend API (if available)  
        3. SMTP (as fallback)
        Returns: True if successful, False otherwise
        """
        try:
            # Try Brevo API first (300 emails/day free)
            if self.brevo_api_key and self.brevo_api_key != 'your_brevo_api_key_here':
                success = self._send_brevo_email(to, subject, body, html)
                if success:
                    return True
            
            # Try Resend API second (3,000 emails/month free)
            if self.api_key:
                success = self._send_resend_email(to, subject, body, html)
                if success:
                    return True
            
            # Fallback to SMTP
            return self._send_smtp_email(to, subject, body, html, attachments)
                
        except Exception as e:
            logger.error(f"Background email service error: {str(e)}")
            return False
    
    def _send_brevo_email(self, to: str, subject: str, body: str, html: Optional[str] = None) -> bool:
        """Send email using Brevo API"""
        try:
            headers = {
                'accept': 'application/json',
                'api-key': self.brevo_api_key,
                'content-type': 'application/json'
            }
            
            email_data = {
                'sender': {
                    'name': 'College Virtual Assistant',
                    'email': self.from_email
                },
                'to': [{'email': to}],
                'subject': subject,
                'htmlContent': html or f"<p>{body.replace(chr(10), '<br>')}</p>"
            }
            
            response = requests.post(
                f'{self.brevo_base_url}/smtp/email',
                headers=headers,
                json=email_data,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Email sent successfully via Brevo to {to}: {subject}")
                return True
            else:
                logger.error(f"Brevo API error: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Brevo API request failed: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Brevo email sending failed: {str(e)}")
            return False
    
    def _send_resend_email(self, to: str, subject: str, body: str, html: Optional[str] = None) -> bool:
        """Send email using Resend API"""
        try:
            email_data = {
                'from': self.from_email,
                'to': [to],
                'subject': subject,
                'text': body
            }
            
            if html:
                email_data['html'] = html
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f'{self.base_url}/emails',
                headers=headers,
                json=email_data,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Email sent successfully via Resend to {to}: {subject}")
                return True
            else:
                logger.error(f"Resend API error: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Resend API request failed: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Resend email sending failed: {str(e)}")
            return False
    
    def _send_smtp_email(self, to: str, subject: str, body: str, html: Optional[str] = None, attachments: Optional[list] = None) -> bool:
        """Send email using SMTP"""
        try:
            # Check if email configuration is complete
            if not all([self.mail_server, self.mail_username, self.mail_password]):
                logger.warning(f"Email configuration incomplete. Email would be sent to {to}: {subject}")
                return True
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to
            
            # Add text and HTML parts
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            if html:
                html_part = MIMEText(html, 'html')
                msg.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                        
                        encoders.encode_base64(part)
                        filename = os.path.basename(file_path)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {filename}'
                        )
                        msg.attach(part)
            
            # Send email with proper SMTP configuration
            server = smtplib.SMTP(self.mail_server, self.mail_port)
            server.set_debuglevel(0)
            server.starttls()
            server.login(self.mail_username, self.mail_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent successfully via SMTP to {to}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"SMTP email sending failed: {str(e)}")
            return False


# Singleton instance for background threads
_background_email_service = None


def get_background_email_service():
    """Get or create background email service instance"""
    global _background_email_service
    if _background_email_service is None:
        _background_email_service = BackgroundEmailService()
    return _background_email_service


def send_email_background(to: str, subject: str, body: str, html: Optional[str] = None, attachments: Optional[list] = None) -> bool:
    """
    Send email from background thread without Flask context
    This is the main function to use from background threads
    """
    service = get_background_email_service()
    return service.send_email(to, subject, body, html, attachments)
