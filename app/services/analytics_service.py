"""
Analytics Service
"""
from collections import Counter
from datetime import datetime, timedelta

from app.extensions import db
from app.models import ChatbotUnknown, ChatbotQA, QueryLog, Student, Session, Result, FeeRecord, Notification


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
        
        # Get unknown queries from past week
        weekly_unknown = ChatbotUnknown.query.filter(
            ChatbotUnknown.created_at >= week_ago
        ).all()
        
        # Get query texts for analysis
        query_texts = [q.query for q in weekly_unknown]
        top_unknown = [item[0] for item in Counter(query_texts).most_common(10)]
        
        return {
            'total_queries': len(query_texts) + ChatbotQA.query.count(),
            'unknown_queries': len(weekly_unknown),
            'top_unknown': top_unknown,
            'report_date': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    @staticmethod
    def get_analytics() -> dict:
        """Get analytics data"""
        try:
            # Simple analytics without complex queries
            return {
                'total_queries': 10,  # Static value for now
                'unknown_queries': 3,  # Static value for now
                'top_unknown': ['help', 'hi', 'hello'],
                'registered_students': Student.query.count(),
                'result_queries_today': 0,
                'fee_queries_today': 0,
                'result_queries_week': 0,
                'fee_queries_week': 0,
            }
        except Exception as e:
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
            }
