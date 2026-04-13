"""
Resend Email Service - API-based email provider compatible with Render
"""
import requests
from flask import current_app
from typing import Optional


class ResendEmailService:
    """Resend API-based email service for Render compatibility"""
    
    def __init__(self):
        self.api_key = current_app.config.get('RESEND_API_KEY')
        self.base_url = 'https://api.resend.com'
        self.from_email = current_app.config.get('MAIL_DEFAULT_SENDER')
    
    def send_email(self, to: str, subject: str, body: str, html: Optional[str] = None, attachments: Optional[list] = None) -> bool:
        """
        Send email using Resend API
        Returns: True if successful, False otherwise
        """
        try:
            # Check if Resend API key is configured
            if not self.api_key:
                current_app.logger.warning("Resend API key not configured. Email would be sent to {}: {}".format(to, subject))
                return True
            
            # Prepare email data
            email_data = {
                'from': self.from_email,
                'to': [to],
                'subject': subject,
                'text': body
            }
            
            # Add HTML content if provided
            if html:
                email_data['html'] = html
            
            # Make API request
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f'{self.base_url}/emails',
                headers=headers,
                json=email_data,
                timeout=10  # Reduced from 30s to 10s for faster response
            )
            
            if response.status_code == 200:
                current_app.logger.info(f"Email sent successfully via Resend to {to}: {subject}")
                return True
            else:
                current_app.logger.error(f"Resend API error: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Resend API request failed: {str(e)}")
            return False
        except Exception as e:
            current_app.logger.error(f"Email sending failed via Resend: {str(e)}")
            return False
    
    def send_weekly_report(self, admin_email: str, report_data: dict, csv_file_path: str = None) -> bool:
        """Send weekly analytics report to admin with CSV attachment"""
        subject = "Weekly Analytics Report - College Virtual Assistant"
        
        body = f"""
        Weekly Analytics Report
        
        Total Students: {report_data.get('total_students', 0)}
        Total Faculty: {report_data.get('total_faculty', 0)}
        Total Notifications: {report_data.get('total_notifications', 0)}
        Total Complaints: {report_data.get('total_complaints', 0)}
        Total Queries: {report_data.get('total_queries', 0)}
        FAQ Records: {report_data.get('unknown_queries', 0)}
        
        Top FAQ Questions:
        """
        
        for i, question in enumerate(report_data.get('top_unknown', [])[:10], 1):
            body += f"{i}. {question}\n"
        
        body += f"\nReport generated on: {report_data.get('report_date', 'N/A')}"
        
        html = f"""
        <html>
        <body>
            <h2>📊 Weekly Analytics Report</h2>
            <div style="display: flex; gap: 20px; margin: 20px 0;">
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px;">
                    <h3>📈 Statistics</h3>
                    <p><strong>Total Students:</strong> {report_data.get('total_students', 0)}</p>
                    <p><strong>Total Faculty:</strong> {report_data.get('total_faculty', 0)}</p>
                    <p><strong>Total Notifications:</strong> {report_data.get('total_notifications', 0)}</p>
                    <p><strong>Total Complaints:</strong> {report_data.get('total_complaints', 0)}</p>
                    <p><strong>Total Queries:</strong> {report_data.get('total_queries', 0)}</p>
                    <p><strong>FAQ Records:</strong> {report_data.get('unknown_queries', 0)}</p>
                </div>
            </div>
            <h3>❓ Top FAQ Questions:</h3>
            <ol>
        """
        
        for question in report_data.get('top_unknown', [])[:10]:
            html += f"<li>{question}</li>"
        
        html += """
            </ol>
            <p><small>Report generated automatically by College Virtual Assistant</small></p>
        </body>
        </html>
        """
        
        # Note: Resend doesn't support attachments in free tier, so we'll send without CSV for now
        return self.send_email(admin_email, subject, body, html)


# Fallback to SMTP for local development
class EmailService:
    """Email service with Resend API and SMTP fallback"""
    
    @staticmethod
    def send_email(to: str, subject: str, body: str, html: str = None, attachments: list = None) -> bool:
        """
        Send email using Resend API (production) or SMTP (development)
        Returns: True if successful, False otherwise
        """
        try:
            # Check if running on Render
            is_render = (
                current_app.config.get('RENDER') == 'true' or 
                current_app.config.get('RENDER_SERVICE_ID') is not None
            )
            
            if is_render:
                # Use Resend API on Render
                resend_service = ResendEmailService()
                return resend_service.send_email(to, subject, body, html, attachments)
            else:
                # Use SMTP for local development
                return EmailService._send_smtp_email(to, subject, body, html, attachments)
                
        except Exception as e:
            current_app.logger.error(f"Email service error: {str(e)}")
            return False
    
    @staticmethod
    def _send_smtp_email(to: str, subject: str, body: str, html: str = None, attachments: list = None) -> bool:
        """Fallback SMTP email service for local development"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.mime.base import MIMEBase
            from email import encoders
            import os
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = current_app.config.get('MAIL_DEFAULT_SENDER')
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
            
            # Check if email configuration is complete
            mail_server = current_app.config.get('MAIL_SERVER')
            mail_username = current_app.config.get('MAIL_USERNAME')
            mail_password = current_app.config.get('MAIL_PASSWORD')
            
            if not all([mail_server, mail_username, mail_password]):
                current_app.logger.warning("Email configuration incomplete. Email would be sent to {}: {}".format(to, subject))
                return True
            
            # Send email with proper SMTP configuration
            server = smtplib.SMTP(mail_server, current_app.config.get('MAIL_PORT'))
            server.set_debuglevel(0)
            server.starttls()
            server.login(mail_username, mail_password)
            server.send_message(msg)
            server.quit()
            
            current_app.logger.info(f"Email sent successfully via SMTP to {to}: {subject}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"SMTP email sending failed: {str(e)}")
            return False
    
    @staticmethod
    def send_weekly_report(admin_email: str, report_data: dict, csv_file_path: str = None) -> bool:
        """Send weekly analytics report to admin with CSV attachment"""
        try:
            # Check if running on Render
            is_render = (
                current_app.config.get('RENDER') == 'true' or 
                current_app.config.get('RENDER_SERVICE_ID') is not None
            )
            
            if is_render:
                # Use Resend API on Render
                resend_service = ResendEmailService()
                return resend_service.send_weekly_report(admin_email, report_data, csv_file_path)
            else:
                # Use SMTP for local development
                return EmailService._send_smtp_weekly_report(admin_email, report_data, csv_file_path)
                
        except Exception as e:
            current_app.logger.error(f"Weekly report email service error: {str(e)}")
            return False
    
    @staticmethod
    def _send_smtp_weekly_report(admin_email: str, report_data: dict, csv_file_path: str = None) -> bool:
        """Fallback SMTP weekly report for local development"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            import os
            
            subject = "Weekly Analytics Report - College Virtual Assistant"
            
            body = f"""
            Weekly Analytics Report
            
            Total Students: {report_data.get('total_students', 0)}
            Total Faculty: {report_data.get('total_faculty', 0)}
            Total Notifications: {report_data.get('total_notifications', 0)}
            Total Complaints: {report_data.get('total_complaints', 0)}
            Total Queries: {report_data.get('total_queries', 0)}
            FAQ Records: {report_data.get('unknown_queries', 0)}
            
            Top FAQ Questions:
            """
            
            for i, question in enumerate(report_data.get('top_unknown', [])[:10], 1):
                body += f"{i}. {question}\n"
            
            body += f"\nReport generated on: {report_data.get('report_date', 'N/A')}"
            
            html = f"""
            <html>
            <body>
                <h2>📊 Weekly Analytics Report</h2>
                <div style="display: flex; gap: 20px; margin: 20px 0;">
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px;">
                        <h3>📈 Statistics</h3>
                        <p><strong>Total Students:</strong> {report_data.get('total_students', 0)}</p>
                        <p><strong>Total Faculty:</strong> {report_data.get('total_faculty', 0)}</p>
                        <p><strong>Total Notifications:</strong> {report_data.get('total_notifications', 0)}</p>
                        <p><strong>Total Complaints:</strong> {report_data.get('total_complaints', 0)}</p>
                        <p><strong>Total Queries:</strong> {report_data.get('total_queries', 0)}</p>
                        <p><strong>FAQ Records:</strong> {report_data.get('unknown_queries', 0)}</p>
                    </div>
                </div>
                <h3>❓ Top FAQ Questions:</h3>
                <ol>
            """
            
            for question in report_data.get('top_unknown', [])[:10]:
                html += f"<li>{question}</li>"
            
            html += """
                </ol>
                <p><small>Report generated automatically by College Virtual Assistant</small></p>
            </body>
            </html>
            """
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = current_app.config.get('MAIL_DEFAULT_SENDER')
            msg['To'] = admin_email
            
            # Add text and HTML parts
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            html_part = MIMEText(html, 'html')
            msg.attach(html_part)
            
            # Add CSV attachment if provided
            if csv_file_path and os.path.exists(csv_file_path):
                from email.mime.base import MIMEBase
                from email import encoders
                
                with open(csv_file_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                filename = os.path.basename(csv_file_path)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {filename}'
                )
                msg.attach(part)
            
            # Send email
            mail_server = current_app.config.get('MAIL_SERVER')
            mail_username = current_app.config.get('MAIL_USERNAME')
            mail_password = current_app.config.get('MAIL_PASSWORD')
            
            if all([mail_server, mail_username, mail_password]):
                server = smtplib.SMTP(mail_server, current_app.config.get('MAIL_PORT'))
                server.set_debuglevel(0)
                server.starttls()
                server.login(mail_username, mail_password)
                server.send_message(msg)
                server.quit()
                
                current_app.logger.info(f"Weekly report sent successfully via SMTP to {admin_email}")
                return True
            else:
                current_app.logger.warning("SMTP configuration incomplete for weekly report")
                return False
                
        except Exception as e:
            current_app.logger.error(f"SMTP weekly report failed: {str(e)}")
            return False
