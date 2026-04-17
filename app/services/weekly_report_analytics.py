"""
Weekly Report Analytics - Data Sent to Admin with Counts
This module provides detailed analytics about what data is sent to admin in weekly reports
including counts, data sources, and export formats.
"""

import os
import csv
import json
from datetime import datetime, timedelta
from collections import Counter
from typing import Dict, List, Any

from app.extensions import db
from app.models import FAQRecord, ChatbotQA, QueryLog, Student, Notification, Result, FeeRecord, Complaint
from app.services.weekly_report_service import WeeklyReportService


class WeeklyReportAnalytics:
    """Analytics service for weekly report data sent to admin"""
    
    def __init__(self):
        self.data_sources = {
            'FAQRecord': FAQRecord,
            'ChatbotQA': ChatbotQA,
            'QueryLog': QueryLog,
            'Student': Student,
            'Notification': Notification,
            'Result': Result,
            'FeeRecord': FeeRecord,
            'Complaint': Complaint
        }
    
    def get_weekly_report_data_breakdown(self) -> Dict[str, Any]:
        """
        Get detailed breakdown of all data sent to admin in weekly reports
        Returns counts, data sources, and content analysis
        """
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        breakdown = {
            'report_metadata': {
                'generated_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                'period_start': week_ago.strftime('%Y-%m-%d %H:%M:%S'),
                'period_end': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                'report_type': 'weekly_analytics'
            },
            'data_sent_to_admin': {
                'email_report': self._get_email_report_data(week_ago),
                'csv_export': self._get_csv_export_data(week_ago),
                'dashboard_metrics': self._get_dashboard_metrics_data(week_ago)
            },
            'data_sources_analysis': self._analyze_data_sources(week_ago),
            'content_analysis': self._analyze_content_patterns(week_ago)
        }
        
        return breakdown
    
    def _get_email_report_data(self, week_ago: datetime) -> Dict[str, Any]:
        """Get data that goes into the email report sent to admin"""
        
        # Get weekly report data (same as WeeklyReportService)
        unknown_queries_count = db.session.query(FAQRecord).filter(
            FAQRecord.created_at >= week_ago
        ).count()
        
        total_chatbot_qa = db.session.query(ChatbotQA).count()
        total_queries = unknown_queries_count + total_chatbot_qa
        
        # Get top unknown queries
        top_unknown = []
        if unknown_queries_count > 0:
            query_texts = [q[0] for q in db.session.query(FAQRecord.query).filter(
                FAQRecord.created_at >= week_ago
            ).all()]
            top_unknown = [item[0] for item in Counter(query_texts).most_common(10)]
        
        return {
            'email_content': {
                'subject': 'Weekly Analytics Report - College Virtual Assistant',
                'recipient': 'admin_email',
                'format': 'text_and_html',
                'data_fields': [
                    {
                        'field_name': 'total_queries',
                        'count': total_queries,
                        'description': 'Total number of queries processed',
                        'calculation': f'unknown_queries({unknown_queries_count}) + chatbot_qa({total_chatbot_qa})'
                    },
                    {
                        'field_name': 'unknown_queries',
                        'count': unknown_queries_count,
                        'description': 'Queries that could not be answered',
                        'source': 'FAQRecord table (created_at >= week_ago)'
                    },
                    {
                        'field_name': 'top_unknown',
                        'count': len(top_unknown),
                        'description': 'Top 10 most frequent unknown queries',
                        'sample_data': top_unknown[:5] if top_unknown else []
                    }
                ]
            },
            'email_size_info': {
                'estimated_text_size': len(f"Total Queries: {total_queries}\nUnknown Queries: {unknown_queries_count}") + 
                                   sum(len(q) for q in top_unknown),
                'html_elements': ['h2', 'div', 'h3', 'p', 'ol', 'li', 'small']
            }
        }
    
    def _get_csv_export_data(self, week_ago: datetime) -> Dict[str, Any]:
        """Get data that goes into the CSV export sent to admin"""
        
        # Get unprocessed FAQ records for CSV export
        unprocessed_records = db.session.query(FAQRecord).filter_by(processed=False).all()
        weekly_records = [r for r in unprocessed_records if r.created_at >= week_ago]
        
        # Analyze CSV data
        csv_data = {
            'file_info': {
                'filename_pattern': 'faq_records_YYYYMMDD_HHMMSS.csv',
                'location': 'data/ directory',
                'encoding': 'utf-8',
                'format': 'CSV'
            },
            'data_structure': {
                'columns': [
                    {'name': 'ID', 'type': 'Integer', 'description': 'Record ID'},
                    {'name': 'Query', 'type': 'Text', 'description': 'The unknown query text'},
                    {'name': 'Phone Number', 'type': 'String', 'description': 'Student phone number (optional)'},
                    {'name': 'Student ID', 'type': 'Integer', 'description': 'Student ID (optional)'},
                    {'name': 'Created At', 'type': 'DateTime', 'description': 'When query was recorded'}
                ],
                'row_count': len(weekly_records),
                'data_size_bytes': sum(len(str(r.id)) + len(r.query or '') + len(r.phone_number or '') + 
                                      len(str(r.student_id or '')) + len(r.created_at.isoformat()) 
                                      for r in weekly_records)
            },
            'content_analysis': {
                'queries_with_phone': len([r for r in weekly_records if r.phone_number]),
                'queries_with_student_id': len([r for r in weekly_records if r.student_id]),
                'unique_queries': len(set(r.query for r in weekly_records if r.query)),
                'duplicate_queries': len(weekly_records) - len(set(r.query for r in weekly_records if r.query)),
                'average_query_length': sum(len(r.query or '') for r in weekly_records) / len(weekly_records) if weekly_records else 0
            }
        }
        
        return csv_data
    
    def _get_dashboard_metrics_data(self, week_ago: datetime) -> Dict[str, Any]:
        """Get dashboard metrics data available to admin"""
        
        # Get various counts for dashboard
        metrics = {
            'student_metrics': {
                'total_students': db.session.query(Student).count(),
                'new_students_week': db.session.query(Student).filter(
                    Student.created_at >= week_ago
                ).count(),
                'telegram_verified_students': db.session.query(Student).filter(
                    Student.telegram_verified == True
                ).count()
            },
            'query_metrics': {
                'total_query_logs': db.session.query(QueryLog).count(),
                'weekly_query_logs': db.session.query(QueryLog).filter(
                    QueryLog.created_at >= week_ago
                ).count() if hasattr(QueryLog, 'created_at') else 0,
                'unknown_queries_total': db.session.query(FAQRecord).count(),
                'unknown_queries_weekly': db.session.query(FAQRecord).filter(
                    FAQRecord.created_at >= week_ago
                ).count()
            },
            'content_metrics': {
                'total_chatbot_qa': db.session.query(ChatbotQA).count(),
                'active_notifications': db.session.query(Notification).filter(
                    Notification.expires_at > datetime.utcnow()
                ).count(),
                'new_notifications_week': db.session.query(Notification).filter(
                    Notification.created_at >= week_ago
                ).count()
            },
            'administrative_metrics': {
                'total_results': db.session.query(Result).count(),
                'total_fee_records': db.session.query(FeeRecord).count(),
                'pending_complaints': db.session.query(Complaint).filter_by(status='pending').count()
            }
        }
        
        return {
            'dashboard_sections': metrics,
            'total_data_points': sum(sum(section.values()) for section in metrics.values()),
            'data_freshness': 'Real-time',
            'update_frequency': 'On-demand refresh'
        }
    
    def _analyze_data_sources(self, week_ago: datetime) -> Dict[str, Any]:
        """Analyze all data sources used in weekly reports"""
        
        analysis = {}
        
        for source_name, model_class in self.data_sources.items():
            try:
                total_count = db.session.query(model_class).count()
                weekly_count = db.session.query(model_class).filter(
                    model_class.created_at >= week_ago
                ).count() if hasattr(model_class, 'created_at') else 0
                
                analysis[source_name] = {
                    'table_name': model_class.__tablename__,
                    'total_records': total_count,
                    'weekly_records': weekly_count,
                    'used_in_report': self._is_used_in_report(source_name),
                    'data_sent_to_admin': self._get_data_sent_for_source(source_name, week_ago)
                }
            except Exception as e:
                analysis[source_name] = {
                    'error': str(e),
                    'table_name': getattr(model_class, '__tablename__', 'Unknown'),
                    'used_in_report': False
                }
        
        return analysis
    
    def _is_used_in_report(self, source_name: str) -> bool:
        """Check if a data source is used in weekly reports"""
        report_sources = ['FAQRecord', 'ChatbotQA']
        return source_name in report_sources
    
    def _get_data_sent_for_source(self, source_name: str, week_ago: datetime) -> Dict[str, Any]:
        """Get specific data sent to admin for each source"""
        
        if source_name == 'FAQRecord':
            records = db.session.query(FAQRecord).filter(
                FAQRecord.created_at >= week_ago
            ).all()
            
            return {
                'email_summary': {
                    'count': len(records),
                    'fields': ['query text aggregation']
                },
                'csv_export': {
                    'count': len([r for r in records if not r.processed]),
                    'fields': ['ID', 'Query', 'Phone Number', 'Student ID', 'Created At']
                }
            }
        
        elif source_name == 'ChatbotQA':
            count = db.session.query(ChatbotQA).count()
            return {
                'email_summary': {
                    'count': count,
                    'fields': ['total count for calculation']
                }
            }
        
        return {'data_sent': 'None'}
    
    def _analyze_content_patterns(self, week_ago: datetime) -> Dict[str, Any]:
        """Analyze content patterns in weekly report data"""
        
        # Get FAQ records for content analysis
        faq_records = db.session.query(FAQRecord).filter(
            FAQRecord.created_at >= week_ago
        ).all()
        
        queries = [r.query for r in faq_records if r.query]
        
        content_analysis = {
            'query_patterns': {
                'total_unique_queries': len(set(queries)),
                'most_common_words': self._get_most_common_words(queries),
                'query_length_distribution': self._get_query_length_distribution(queries),
                'potential_categories': self._categorize_queries(queries)
            },
            'data_quality': {
                'queries_with_phone_percentage': (len([r for r in faq_records if r.phone_number]) / len(faq_records) * 100) if faq_records else 0,
                'queries_with_student_id_percentage': (len([r for r in faq_records if r.student_id]) / len(faq_records) * 100) if faq_records else 0,
                'empty_queries': len([r for r in faq_records if not r.query or not r.query.strip()])
            }
        }
        
        return content_analysis
    
    def _get_most_common_words(self, queries: List[str], top_n: int = 10) -> List[Dict[str, Any]]:
        """Get most common words from queries"""
        if not queries:
            return []
        
        # Simple word frequency analysis
        all_words = []
        for query in queries:
            words = query.lower().split()
            all_words.extend([word.strip('.,!?') for word in words if len(word) > 2])
        
        word_counts = Counter(all_words)
        return [{'word': word, 'count': count} for word, count in word_counts.most_common(top_n)]
    
    def _get_query_length_distribution(self, queries: List[str]) -> Dict[str, int]:
        """Get distribution of query lengths"""
        if not queries:
            return {}
        
        lengths = [len(q) for q in queries]
        
        return {
            'short_1_20': len([l for l in lengths if l <= 20]),
            'medium_21_50': len([l for l in lengths if 21 <= l <= 50]),
            'long_51_100': len([l for l in lengths if 51 <= l <= 100]),
            'very_long_100_plus': len([l for l in lengths if l > 100]),
            'average_length': sum(lengths) / len(lengths)
        }
    
    def _categorize_queries(self, queries: List[str]) -> Dict[str, int]:
        """Simple categorization of queries based on keywords"""
        categories = {
            'fees': 0,
            'results': 0,
            'admission': 0,
            'courses': 0,
            'faculty': 0,
            'general': 0
        }
        
        category_keywords = {
            'fees': ['fee', 'payment', 'cost', 'fees', 'paid', 'due'],
            'results': ['result', 'mark', 'grade', 'score', 'exam'],
            'admission': ['admission', 'apply', 'join', 'enroll'],
            'courses': ['course', 'subject', 'syllabus', 'curriculum'],
            'faculty': ['teacher', 'professor', 'faculty', 'staff']
        }
        
        for query in queries:
            query_lower = query.lower()
            categorized = False
            
            for category, keywords in category_keywords.items():
                if any(keyword in query_lower for keyword in keywords):
                    categories[category] += 1
                    categorized = True
                    break
            
            if not categorized:
                categories['general'] += 1
        
        return categories
    
    def generate_analytics_report(self, output_format: str = 'json') -> str:
        """Generate complete analytics report and save to file"""
        
        breakdown = self.get_weekly_report_data_breakdown()
        
        # Create reports directory if it doesn't exist
        reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        
        if output_format.lower() == 'json':
            filename = f'weekly_report_analytics_{timestamp}.json'
            filepath = os.path.join(reports_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(breakdown, f, indent=2, default=str)
        
        elif output_format.lower() == 'csv':
            filename = f'weekly_report_analytics_{timestamp}.csv'
            filepath = os.path.join(reports_dir, filename)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write summary section
                writer.writerow(['Weekly Report Analytics Summary'])
                writer.writerow(['Generated At', breakdown['report_metadata']['generated_at']])
                writer.writerow([])
                
                # Write email report data
                writer.writerow(['Email Report Data'])
                for field in breakdown['data_sent_to_admin']['email_report']['email_content']['data_fields']:
                    writer.writerow([field['field_name'], field['count'], field['description']])
                writer.writerow([])
                
                # Write CSV export data
                writer.writerow(['CSV Export Data'])
                writer.writerow(['Records Count', breakdown['data_sent_to_admin']['csv_export']['data_structure']['row_count']])
                writer.writerow(['File Size (bytes)', breakdown['data_sent_to_admin']['csv_export']['data_structure']['data_size_bytes']])
                writer.writerow([])
                
                # Write data sources analysis
                writer.writerow(['Data Sources Analysis'])
                for source, data in breakdown['data_sources_analysis'].items():
                    if 'error' not in data:
                        writer.writerow([source, data['total_records'], data['weekly_records'], str(data['used_in_report'])])
        
        return filepath
    
    def get_data_summary_for_admin(self) -> str:
        """Get a human-readable summary of data sent to admin"""
        
        breakdown = self.get_weekly_report_data_breakdown()
        
        summary = f"""
WEEKLY REPORT DATA SENT TO ADMIN - SUMMARY
==========================================

Report Generated: {breakdown['report_metadata']['generated_at']}
Period: {breakdown['report_metadata']['period_start']} to {breakdown['report_metadata']['period_end']}

1. EMAIL REPORT DATA:
-------------------
- Total Queries: {breakdown['data_sent_to_admin']['email_report']['email_content']['data_fields'][0]['count']}
- Unknown Queries: {breakdown['data_sent_to_admin']['email_report']['email_content']['data_fields'][1]['count']}
- Top Unknown Questions: {breakdown['data_sent_to_admin']['email_report']['email_content']['data_fields'][2]['count']} items

2. CSV EXPORT DATA:
------------------
- Records Exported: {breakdown['data_sent_to_admin']['csv_export']['data_structure']['row_count']}
- File Size: {breakdown['data_sent_to_admin']['csv_export']['data_structure']['data_size_bytes']} bytes
- Columns: ID, Query, Phone Number, Student ID, Created At

3. DASHBOARD METRICS:
---------------------
- Total Data Points: {breakdown['data_sent_to_admin']['dashboard_metrics']['total_data_points']}
- Update Frequency: {breakdown['data_sent_to_admin']['dashboard_metrics']['update_frequency']}

4. DATA SOURCES USED:
---------------------
"""
        
        for source, data in breakdown['data_sources_analysis'].items():
            if data.get('used_in_report'):
                summary += f"- {source}: {data['weekly_records']} weekly records\n"
        
        summary += f"""
5. CONTENT ANALYSIS:
-------------------
- Unique Queries: {breakdown['content_analysis']['query_patterns']['total_unique_queries']}
- Queries with Phone: {breakdown['content_analysis']['data_quality']['queries_with_phone_percentage']:.1f}%
- Queries with Student ID: {breakdown['content_analysis']['data_quality']['queries_with_student_id_percentage']:.1f}%
"""
        
        return summary


# Convenience function for quick analytics
def get_weekly_report_analytics():
    """Quick function to get weekly report analytics"""
    analytics = WeeklyReportAnalytics()
    return analytics.get_weekly_report_data_breakdown()


# Convenience function for admin summary
def get_admin_data_summary():
    """Quick function to get admin data summary"""
    analytics = WeeklyReportAnalytics()
    return analytics.get_data_summary_for_admin()
