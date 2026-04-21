"""
Weekly Report Service
"""
import csv
import os
import logging
from datetime import datetime, timedelta

from app.extensions import db
from app.models import FAQRecord, ChatbotQA, VisitorQuery
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
            
            # Export visitor queries to CSV (only if there are any)
            visitor_csv_path = None
            if report_data.get('visitor_queries', {}).get('total_queries', 0) > 0:
                visitor_csv_path = WeeklyReportService._export_visitor_queries_csv_optimized()
            
            # Prepare attachments list
            attachments = []
            if csv_path and os.path.exists(csv_path):
                if isinstance(csv_path, str):
                    attachments.append(csv_path)
                else:
                    logger.error(f"CSV path is not a string: {type(csv_path)} - {csv_path}")
            if visitor_csv_path and os.path.exists(visitor_csv_path):
                if isinstance(visitor_csv_path, str):
                    attachments.append(visitor_csv_path)
                else:
                    logger.error(f"Visitor CSV path is not a string: {type(visitor_csv_path)} - {visitor_csv_path}")
            
            # Send email to admin using background service with attachments
            WeeklyReportService._send_weekly_report_background(report_data, attachments)
            
            # Mark queries as processed (batch update for memory efficiency)
            WeeklyReportService._mark_queries_processed_optimized()
            
            logger.info(f"Weekly report generated successfully. Unknown queries: {report_data.get('unknown_queries', 0)}, Visitor queries: {report_data.get('visitor_queries', {}).get('total_queries', 0)}")
            return csv_path, visitor_csv_path
            
        except Exception as e:
            logger.error(f"Error generating weekly report: {str(e)}")
            return None, None
    
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
    def _export_unknown_queries_csv_optimized() -> str:
        """Export unknown queries to CSV with memory optimization"""
        try:
            # Ensure data directory exists
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
            os.makedirs(data_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            csv_filename = f'faq_records_{timestamp}.csv'
            csv_path = os.path.join(data_dir, csv_filename)
            
            # Use batched queries to avoid memory issues
            batch_size = 1000
            offset = 0
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['ID', 'Query', 'Phone Number', 'Student ID', 'Created At'])
                
                while True:
                    # Get batch of records
                    batch = db.session.query(FAQRecord).filter_by(processed=False).offset(offset).limit(batch_size).all()
                    if not batch:
                        break
                    
                    # Write batch to CSV
                    for query in batch:
                        writer.writerow([
                            query.id,
                            query.query,
                            query.phone_number or '',
                            query.student_id or '',
                            query.created_at.isoformat()
                        ])
                    
                    offset += batch_size
                    # Clear session to free memory
                    db.session.expunge_all()
            
            return csv_path
        except Exception as e:
            logger.error(f"Error exporting unknown queries CSV: {str(e)}")
            return None
    
    @staticmethod
    def _export_visitor_queries_csv_optimized() -> str:
        """Export visitor queries to CSV with memory optimization"""
        try:
            # Ensure data directory exists
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
            os.makedirs(data_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            csv_filename = f'visitor_queries_{timestamp}.csv'
            csv_path = os.path.join(data_dir, csv_filename)
            
            # Get visitor queries from the last week
            week_ago = datetime.utcnow() - timedelta(days=7)
            
            # Use batched queries to avoid memory issues
            batch_size = 1000
            offset = 0
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['ID', 'Query Type', 'Query Text', 'Response Text', 'Phone Number', 'Telegram User ID', 'Created At'])
                
                while True:
                    # Get batch of records (excluding visitors with telegram mappings)
                    batch = db.session.query(VisitorQuery).filter(
                        VisitorQuery.created_at >= week_ago,
                        VisitorQuery.telegram_user_id.is_(None)  # Exclude visitors with telegram mappings
                    ).offset(offset).limit(batch_size).all()
                    if not batch:
                        break
                    
                    # Write batch to CSV
                    for query in batch:
                        writer.writerow([
                            query.id,
                            query.query_type,
                            query.query_text,
                            query.response_text,
                            query.phone_number or '',
                            query.telegram_user_id or '',
                            query.created_at.isoformat()
                        ])
                    
                    offset += batch_size
                    # Clear session to free memory
                    db.session.expunge_all()
            
            return csv_path
        except Exception as e:
            logger.error(f"Error exporting visitor queries CSV: {str(e)}")
            return None
    
    @staticmethod
    def _get_weekly_report_data_optimized() -> dict:
        """Get weekly report data with memory optimization"""
        try:
            week_ago = datetime.utcnow() - timedelta(days=7)
            
            # Use count() instead of loading all records for memory efficiency
            unknown_queries_count = db.session.query(FAQRecord).filter(
                FAQRecord.created_at >= week_ago
            ).count()
            
            # Get visitor queries analytics
            visitor_queries_data = WeeklyReportService._get_visitor_queries_analytics(week_ago)
            
            # Get only the top queries without loading all records
            from collections import Counter
            top_unknown = []
            if unknown_queries_count > 0:
                # Get only the query texts, not full objects
                query_texts = [q.query for q in db.session.query(FAQRecord).filter(
                    FAQRecord.created_at >= week_ago
                ).all()]
                top_unknown = [item[0] for item in Counter(query_texts).most_common(10)]
            
            return {
                'total_queries': unknown_queries_count + (db.session.query(ChatbotQA).count() or 0),
                'unknown_queries': unknown_queries_count,
                'top_unknown': top_unknown,
                'visitor_queries': visitor_queries_data,
                'report_date': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            logger.error(f"Error getting weekly report data: {str(e)}")
            return {
                'total_queries': 0,
                'unknown_queries': 0,
                'top_unknown': [],
                'visitor_queries': {
                    'total_queries': 0,
                    'query_types': {},
                    'top_queries': []
                },
                'report_date': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    @staticmethod
    def _get_visitor_queries_analytics(week_ago: datetime) -> dict:
        """Get visitor queries analytics for targeting audience insights"""
        try:
            # Get visitor queries from the last week, excluding those with telegram ID mappings
            # (exclude visitors who are already verified students)
            visitor_queries = db.session.query(VisitorQuery).filter(
                VisitorQuery.created_at >= week_ago,
                VisitorQuery.telegram_user_id.is_(None)  # Exclude visitors with telegram mappings
            ).all()
            
            # Count queries by type (focus on admission-related categories)
            target_types = ['admission', 'course', 'contact', 'facilities', 'faculty']
            query_type_counts = {}
            
            # Initialize all target types with 0
            for query_type in target_types:
                query_type_counts[query_type] = 0
            
            # Count actual queries by type
            for query in visitor_queries:
                query_type = query.query_type.lower()
                if query_type in target_types:
                    query_type_counts[query_type] += 1
                else:
                    # Group other types as 'other'
                    query_type_counts['other'] = query_type_counts.get('other', 0) + 1
            
            # Get top visitor queries for insights
            from collections import Counter
            query_texts = [q.query_text for q in visitor_queries if q.query_text]
            top_queries = [item[0] for item in Counter(query_texts).most_common(10)]
            
            # Calculate unique visitors (only by phone number, since we exclude telegram users)
            unique_visitors = set()
            for query in visitor_queries:
                if query.phone_number:
                    unique_visitors.add(f"phone:{query.phone_number}")
            
            return {
                'total_queries': len(visitor_queries),
                'unique_visitors': len(unique_visitors),
                'query_types': query_type_counts,
                'top_queries': top_queries,
                'targeting_insights': {
                    'admission_interest': query_type_counts.get('admission', 0),
                    'course_inquiry': query_type_counts.get('course', 0),
                    'contact_requests': query_type_counts.get('contact', 0),
                    'facilities_interest': query_type_counts.get('facilities', 0),
                    'faculty_inquiry': query_type_counts.get('faculty', 0),
                    'total_target_queries': sum(query_type_counts.get(t, 0) for t in target_types)
                },
                'excluded_telegram_users': True,  # Flag to indicate telegram users are excluded
                'note': 'Visitors with Telegram ID mappings (verified students) are excluded from this analysis'
            }
        except Exception as e:
            logger.error(f"Error getting visitor queries analytics: {str(e)}")
            return {
                'total_queries': 0,
                'unique_visitors': 0,
                'query_types': {},
                'top_queries': [],
                'targeting_insights': {
                    'admission_interest': 0,
                    'course_inquiry': 0,
                    'contact_requests': 0,
                    'facilities_interest': 0,
                    'faculty_inquiry': 0,
                    'total_target_queries': 0
                },
                'excluded_telegram_users': True,
                'note': 'Visitors with Telegram ID mappings (verified students) are excluded from this analysis'
            }
    
    @staticmethod
    def _send_weekly_report_background(report_data: dict, attachments: list = None):
        """Send weekly report email using background service"""
        try:
            # Create email content
            subject = "Weekly Analytics Report - College Virtual Assistant"
            
            # Get visitor queries data
            visitor_data = report_data.get('visitor_queries', {})
            targeting_insights = visitor_data.get('targeting_insights', {})
            
            body = f"""
            Weekly Analytics Report
            
            Total Queries: {report_data.get('total_queries', 0)}
            Unknown Queries: {report_data.get('unknown_queries', 0)}
            
            VISITOR QUERIES ANALYSIS (For Targeting Audience):
            ===============================================
            Total Visitor Queries: {visitor_data.get('total_queries', 0)}
            Unique Visitors: {visitor_data.get('unique_visitors', 0)}
            *Note: Verified students (with Telegram accounts) are excluded from this analysis*
            
            Query Type Breakdown:
            - Admission Interest: {targeting_insights.get('admission_interest', 0)}
            - Course Inquiries: {targeting_insights.get('course_inquiry', 0)}
            - Contact Requests: {targeting_insights.get('contact_requests', 0)}
            - Facilities Interest: {targeting_insights.get('facilities_interest', 0)}
            - Faculty Inquiries: {targeting_insights.get('faculty_inquiry', 0)}
            
            Targeting Insights:
            Total Target Queries: {targeting_insights.get('total_target_queries', 0)}
            Admission Conversion Potential: {targeting_insights.get('admission_interest', 0)} visitors
            
            Top FAQ Questions:
            """
            
            for i, question in enumerate(report_data.get('top_unknown', [])[:10], 1):
                body += f"{i}. {question}\n"
            
            body += f"\nTop Visitor Queries:\n"
            for i, query in enumerate(visitor_data.get('top_queries', [])[:5], 1):
                body += f"{i}. {query}\n"
            
            body += f"\nReport generated on: {report_data.get('report_date', 'N/A')}"
            
            # Create HTML version
            html = f"""
            <html>
            <body>
                <h2>Weekly Analytics Report</h2>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h3>General Statistics</h3>
                    <p><strong>Total Queries:</strong> {report_data.get('total_queries', 0)}</p>
                    <p><strong>Unknown Queries:</strong> {report_data.get('unknown_queries', 0)}</p>
                </div>
                
                <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #28a745;">
                    <h3>Visitor Queries Analysis (Targeting Audience Insights)</h3>
                    <p><strong>Total Visitor Queries:</strong> {visitor_data.get('total_queries', 0)}</p>
                    <p><strong>Unique Visitors:</strong> {visitor_data.get('unique_visitors', 0)}</p>
                    <p><small><em>Note: Verified students (with Telegram accounts) are excluded from this analysis</em></small></p>
                    
                    <h4>Query Type Breakdown:</h4>
                    <ul style="margin: 10px 0;">
                        <li><strong>Admission Interest:</strong> {targeting_insights.get('admission_interest', 0)}</li>
                        <li><strong>Course Inquiries:</strong> {targeting_insights.get('course_inquiry', 0)}</li>
                        <li><strong>Contact Requests:</strong> {targeting_insights.get('contact_requests', 0)}</li>
                        <li><strong>Facilities Interest:</strong> {targeting_insights.get('facilities_interest', 0)}</li>
                        <li><strong>Faculty Inquiries:</strong> {targeting_insights.get('faculty_inquiry', 0)}</li>
                    </ul>
                    
                    <div style="background: #fff3cd; padding: 10px; border-radius: 5px; margin: 10px 0;">
                        <h4>Targeting Insights:</h4>
                        <p><strong>Total Target Queries:</strong> {targeting_insights.get('total_target_queries', 0)}</p>
                        <p><strong>Admission Conversion Potential:</strong> {targeting_insights.get('admission_interest', 0)} visitors</p>
                    </div>
                </div>
                
                <h3>Top FAQ Questions:</h3>
                <ol>
            """
            
            for question in report_data.get('top_unknown', [])[:10]:
                html += f"<li>{question}</li>"
            
            html += "</ol>"
            
            if visitor_data.get('top_queries'):
                html += "<h3>Top Visitor Queries:</h3><ol>"
                for query in visitor_data.get('top_queries', [])[:5]:
                    html += f"<li>{query}</li>"
                html += "</ol>"
            
            html += """
                <p><small>Report generated automatically by College Virtual Assistant</small></p>
            </body>
            </html>
            """
            
            # Send using background email service
            admin_email = Config.ADMIN_EMAIL or 'uniyalanuj1@gmail.com'
            logger.info(f"Attempting to send weekly report with {len(attachments) if attachments else 0} attachments")
            if attachments:
                for i, attachment in enumerate(attachments):
                    logger.info(f"Attachment {i+1}: {attachment} (type: {type(attachment)})")
            
            success = send_email_background(admin_email, subject, body, html, attachments)
            
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
