"""
Weekly Report Service
"""
import csv
import os
from datetime import datetime, timedelta

from app.extensions import db
from app.models import FAQRecord
from app.services.analytics_service import AnalyticsService
from app.services.email_service import EmailService
from app.config import Config


class WeeklyReportService:
    """Weekly report generation and export service"""
    
    @staticmethod
    def generate_weekly_report():
        """Generate and export weekly report"""
        # Get report data
        report_data = AnalyticsService.get_weekly_report_data()
        
        # Export unknown queries to CSV
        csv_path = WeeklyReportService.export_unknown_queries_csv()
        
        # Send email to admin
        EmailService.send_weekly_report(Config.ADMIN_EMAIL, report_data)
        
        # Mark queries as processed
        week_ago = datetime.utcnow() - timedelta(days=7)
        db.session.query(FAQRecord).filter(
            FAQRecord.created_at >= week_ago,
            FAQRecord.processed == False
        ).update({'processed': True})
        db.session.commit()
        
        return csv_path
    
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
