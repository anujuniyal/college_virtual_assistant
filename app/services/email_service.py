"""
Email Service
"""
from flask import current_app
from app.config import Config
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailService:
    """Email sending service"""
    
    @staticmethod
    def send_email(to: str, subject: str, body: str, html: str = None) -> bool:
        """
        Send email
        Returns: True if successful, False otherwise
        """
        try:
            # Simple SMTP implementation (can be replaced with Flask-Mail)
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = Config.MAIL_DEFAULT_SENDER
            msg['To'] = to
            
            # Add text and HTML parts
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            if html:
                html_part = MIMEText(html, 'html')
                msg.attach(html_part)
            
            # Send email
            if Config.MAIL_SERVER and Config.MAIL_USERNAME and Config.MAIL_PASSWORD:
                server = smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT)
                server.starttls()
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                server.send_message(msg)
                server.quit()
                return True
            else:
                # Log email in development (no actual sending)
                current_app.logger.info(f"Email would be sent to {to}: {subject}")
                return True
        except Exception as e:
            current_app.logger.error(f"Email sending failed: {str(e)}")
            return False
    
    @staticmethod
    def send_weekly_report(admin_email: str, report_data: dict) -> bool:
        """Send weekly analytics report to admin"""
        subject = "Weekly Analytics Report - College Virtual Assistant"
        
        body = f"""
        Weekly Analytics Report
        
        Total Queries: {report_data.get('total_queries', 0)}
        Unknown Queries: {report_data.get('unknown_queries', 0)}
        Top Unknown Questions:
        """
        
        for i, question in enumerate(report_data.get('top_unknown', [])[:10], 1):
            body += f"{i}. {question}\n"
        
        body += f"\nReport generated on: {report_data.get('report_date', 'N/A')}"
        
        html = f"""
        <html>
        <body>
            <h2>Weekly Analytics Report</h2>
            <p><strong>Total Queries:</strong> {report_data.get('total_queries', 0)}</p>
            <p><strong>Unknown Queries:</strong> {report_data.get('unknown_queries', 0)}</p>
            <h3>Top Unknown Questions:</h3>
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
        
        return EmailService.send_email(admin_email, subject, body, html)
