"""
Email Service
"""
from flask import current_app
from app.config import Config
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os


class EmailService:
    """Email sending service"""
    
    @staticmethod
    def send_email(to: str, subject: str, body: str, html: str = None, attachments: list = None) -> bool:
        """
        Send email with optional attachments
        Returns: True if successful, False otherwise
        """
        try:
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
            
            # Enable debug logging for troubleshooting
            server.set_debuglevel(1)
            
            # Start TLS encryption
            server.starttls()
            
            # Login with credentials
            server.login(mail_username, mail_password)
            
            # Send message
            server.send_message(msg)
            server.quit()
            
            current_app.logger.info(f"Email sent successfully to {to}: {subject}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            current_app.logger.error(f"SMTP Authentication Error: {str(e)}")
            current_app.logger.error("Please check your Gmail username and app password")
            return False
        except smtplib.SMTPException as e:
            current_app.logger.error(f"SMTP Error: {str(e)}")
            return False
        except Exception as e:
            current_app.logger.error(f"Email sending failed: {str(e)}")
            return False
    
    @staticmethod
    def send_weekly_report(admin_email: str, report_data: dict, csv_file_path: str = None) -> bool:
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
        
        # Add CSV attachment if provided
        attachments = [csv_file_path] if csv_file_path and os.path.exists(csv_file_path) else None
        
        return EmailService.send_email(admin_email, subject, body, html, attachments)
