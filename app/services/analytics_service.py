"""
Analytics Service
"""
from collections import Counter
from datetime import datetime, timedelta
from flask import current_app

from app.extensions import db
from app.models import FAQRecord, ChatbotQA, QueryLog, Student, Session, Result, FeeRecord, Notification, VisitorQuery


class AnalyticsService:
    """Analytics and reporting service"""
    
    @staticmethod
    def track_query():
        """Track a chatbot query"""
        # This is called when a query is made
        # Additional tracking can be added here
        pass
    
    @staticmethod
    def get_weekly_report_data() -> dict:
        """Get data for weekly report"""
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        # Get FAQ records from past week
        weekly_unknown = db.session.query(FAQRecord).filter(
            FAQRecord.created_at >= week_ago
        ).all()
        
        # Get query texts for analysis
        query_texts = [q.query for q in weekly_unknown]
        top_unknown = [item[0] for item in Counter(query_texts).most_common(10)]
        
        return {
            'total_queries': len(query_texts) + db.session.query(ChatbotQA).count(),
            'unknown_queries': len(weekly_unknown),
            'top_unknown': top_unknown,
            'report_date': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    @staticmethod
    def get_dashboard_analytics() -> dict:
        """Get dashboard analytics data"""
        try:
            # Initialize default values
            analytics_data = {
                'total_queries': 0,
                'unknown_queries': 0,
                'registered_students': 0,
                'result_queries_today': 0,
                'fee_queries_today': 0,
                'result_queries_week': 0,
                'fee_queries_week': 0,
            }
            
            # Get query logs count with error handling
            try:
                analytics_data['total_queries'] = db.session.query(QueryLog).count()
            except Exception as e:
                current_app.logger.warning(f"QueryLog query failed in dashboard: {e}")
                analytics_data['total_queries'] = 0
            
            # Get FAQ records count with error handling
            try:
                analytics_data['unknown_queries'] = db.session.query(FAQRecord).count()
            except Exception as e:
                current_app.logger.warning(f"FAQRecord query failed in dashboard: {e}")
                analytics_data['unknown_queries'] = 0
            
            # Get student count with error handling
            try:
                analytics_data['registered_students'] = db.session.query(Student).count()
            except Exception as e:
                current_app.logger.warning(f"Student query failed in dashboard: {e}")
                analytics_data['registered_students'] = 0
            
            return analytics_data
            
        except Exception as e:
            current_app.logger.error(f"Dashboard analytics error: {e}")
            # Return default values if there's an error
            return {
                'total_queries': 0,
                'unknown_queries': 0,
                'registered_students': 0,
                'result_queries_today': 0,
                'fee_queries_today': 0,
                'result_queries_week': 0,
                'fee_queries_week': 0,
            }
    
    @staticmethod
    def get_analytics(period='7days') -> dict:
        """Get analytics data"""
        try:
            # Initialize default values
            analytics_data = {
                'total_queries': 0,
                'unknown_queries': 0,
                'top_unknown': [],
                'registered_students': 0,
                'result_queries_today': 0,
                'fee_queries_today': 0,
                'result_queries_week': 0,
                'fee_queries_week': 0,
            }
            
            # Get query logs count with error handling
            try:
                analytics_data['total_queries'] = db.session.query(QueryLog).count()
            except Exception as e:
                current_app.logger.warning(f"QueryLog query failed: {e}")
                analytics_data['total_queries'] = 0
            
            # Get FAQ records count with error handling (unknown queries)
            try:
                analytics_data['unknown_queries'] = db.session.query(FAQRecord).count()
            except Exception as e:
                current_app.logger.warning(f"FAQRecord query failed: {e}")
                analytics_data['unknown_queries'] = 0
            
            # Get student count with error handling
            try:
                analytics_data['registered_students'] = db.session.query(Student).count()
            except Exception as e:
                current_app.logger.warning(f"Student query failed: {e}")
                analytics_data['registered_students'] = 0
            
            # Calculate success rate
            if analytics_data['total_queries'] > 0:
                answered_queries = analytics_data['total_queries'] - analytics_data['unknown_queries']
                analytics_data['success_rate'] = round((answered_queries / analytics_data['total_queries']) * 100)
            else:
                analytics_data['success_rate'] = 0
            
            return analytics_data
            
        except Exception as e:
            current_app.logger.error(f"Analytics error: {e}")
            # Return default values if there's an error
            return {
                'total_queries': 0,
                'unknown_queries': 0,
                'top_unknown': [],
                'registered_students': 0,
                'result_queries_today': 0,
                'fee_queries_today': 0,
                'result_queries_week': 0,
                'fee_queries_week': 0,
                'success_rate': 0,
            }
