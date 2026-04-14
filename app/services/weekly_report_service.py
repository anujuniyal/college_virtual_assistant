"""
Weekly Report Service
"""
import csv
import os
import logging
from datetime import datetime, timedelta

from app.extensions import db
from app.models import FAQRecord
from app.services.analytics_service import AnalyticsService
from app.services.background_email_service import send_email_background
from app.config import Config

logger = logging.getLogger(__name__)


class WeeklyReportService:
    """Weekly report generation and export service"""
    
    @staticmethod
    def generate_weekly_report():
        """Generate and export weekly report"""
        try:
            # Get report data with memory optimization
            report_data = WeeklyReportService._get_weekly_report_data_optimized()
            
            # Export unknown queries to CSV (only if there are any)
            csv_path = None
            if report_data.get('unknown_queries', 0) > 0:
                csv_path = WeeklyReportService._export_unknown_queries_csv_optimized()
            
            # Send email to admin using background service
            WeeklyReportService._send_weekly_report_background(report_data)
            
            # Mark queries as processed (batch update for memory efficiency)
            WeeklyReportService._mark_queries_processed_optimized()
            
            logger.info(f"Weekly report generated successfully. Unknown queries: {report_data.get('unknown_queries', 0)}")
            return csv_path
            
        except Exception as e:
            logger.error(f"Error generating weekly report: {str(e)}")
            return None
    
    @staticmethod
    def export_unknown_queries_csv() -> str:
        """Export unknown queries to CSV"""
        # Ensure data directory exists
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        # Get unprocessed queries
        unknown_queries = db.session.query(FAQRecord).filter_by(processed=False).all()
        
        # Generate filename with timestamp
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        csv_filename = f'faq_records_{timestamp}.csv'
        csv_path = os.path.join(data_dir, csv_filename)
        
        # Write to CSV
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['ID', 'Query', 'Phone Number', 'Student ID', 'Created At'])
            
            for query in unknown_queries:
                writer.writerow([
                    query.id,
                    query.query,
                    query.phone_number or '',
                    query.student_id or '',
                    query.created_at.isoformat()
                ])
        
        return csv_path
    
    @staticmethod
    def _get_weekly_report_data_optimized() -> dict:
        """Get weekly report data with memory optimization"""
        try:
            week_ago = datetime.utcnow() - timedelta(days=7)
            
            # Use count() instead of loading all records for memory efficiency
            unknown_queries_count = db.session.query(FAQRecord).filter(
                FAQRecord.created_at >= week_ago
            ).count()
            
            # Get only the top queries without loading all records
            from collections import Counter
            top_unknown = []
            if unknown_queries_count > 0:
                # Get only the query texts, not full objects
                query_texts = [q[0] for q in db.session.query(FAQRecord.query).filter(
                    FAQRecord.created_at >= week_ago
                ).all()]
                top_unknown = [item[0] for item in Counter(query_texts).most_common(10)]
            
            return {
                'total_queries': unknown_queries_count + (db.session.query(ChatbotQA).count() or 0),
                'unknown_queries': unknown_queries_count,
                'top_unknown': top_unknown,
                'report_date': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            logger.error(f"Error getting weekly report data: {str(e)}")
            return {
                'total_queries': 0,
                'unknown_queries': 0,
                'top_unknown': [],
                'report_date': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    @staticmethod
    def _send_weekly_report_background(report_data: dict):
        """Send weekly report email using background service"""
        try:
            # Create email content
            subject = "Weekly Analytics Report - College Virtual Assistant"
            
            body = f"""
            Weekly Analytics Report
            
            Total Queries: {report_data.get('total_queries', 0)}
            Unknown Queries: {report_data.get('unknown_queries', 0)}
            
            Top FAQ Questions:
            """
            
            for i, question in enumerate(report_data.get('top_unknown', [])[:10], 1):
                body += f"{i}. {question}\n"
            
            body += f"\nReport generated on: {report_data.get('report_date', 'N/A')}"
            
            # Create HTML version
            html = f"""
            <html>
            <body>
                <h2>Weekly Analytics Report</h2>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h3>Statistics</h3>
                    <p><strong>Total Queries:</strong> {report_data.get('total_queries', 0)}</p>
                    <p><strong>Unknown Queries:</strong> {report_data.get('unknown_queries', 0)}</p>
                </div>
                <h3>Top FAQ Questions:</h3>
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
            
            # Send using background email service
            admin_email = Config.ADMIN_EMAIL or 'uniyalanuj1@gmail.com'
            success = send_email_background(admin_email, subject, body, html)
            
            if success:
                logger.info(f"Weekly report email sent successfully to {admin_email}")
            else:
                logger.error(f"Failed to send weekly report email to {admin_email}")
                
        except Exception as e:
            logger.error(f"Error sending weekly report email: {str(e)}")
    
    @staticmethod
    def _mark_queries_processed_optimized():
        """Mark queries as processed with memory optimization"""
        try:
            week_ago = datetime.utcnow() - timedelta(days=7)
            
            # Use batch update instead of loading all records
            result = db.session.query(FAQRecord).filter(
                FAQRecord.created_at >= week_ago,
                FAQRecord.processed == False
            ).update({'processed': True}, synchronize_session=False)
            
            db.session.commit()
            logger.info(f"Marked {result} queries as processed")
            
        except Exception as e:
            logger.error(f"Error marking queries as processed: {str(e)}")
            db.session.rollback()
