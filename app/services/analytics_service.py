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
        
        # Get visitor queries analytics (excluding verified students)
        visitor_data = AnalyticsService._get_visitor_queries_analytics()
        
        return {
            'total_queries': len(query_texts) + db.session.query(ChatbotQA).count(),
            'unknown_queries': len(weekly_unknown),
            'top_unknown': top_unknown,
            'visitor_queries': visitor_data,
            'report_date': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    @staticmethod
    def _get_visitor_queries_analytics() -> dict:
        """Get visitor queries analytics for targeting insights"""
        try:
            week_ago = datetime.utcnow() - timedelta(days=7)
            
            # Get visitor queries from the last week (excluding verified students)
            visitor_queries = db.session.query(VisitorQuery).filter(
                VisitorQuery.created_at >= week_ago,
                VisitorQuery.telegram_user_id.is_(None)  # Exclude visitors with telegram mappings
            ).all()
            
            if not visitor_queries:
                return {
                    'total_queries': 0,
                    'unique_visitors': 0,
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
            
            # Count total queries and unique visitors
            total_queries = len(visitor_queries)
            unique_visitors = len(set(vq.phone_number for vq in visitor_queries if vq.phone_number))
            
            # Categorize queries by type
            targeting_insights = {
                'admission_interest': 0,
                'course_inquiry': 0,
                'contact_requests': 0,
                'facilities_interest': 0,
                'faculty_inquiry': 0,
                'total_target_queries': 0
            }
            
            for vq in visitor_queries:
                query_type = vq.query_type.lower()
                if query_type == 'admission':
                    targeting_insights['admission_interest'] += 1
                    targeting_insights['total_target_queries'] += 1
                elif query_type == 'course':
                    targeting_insights['course_inquiry'] += 1
                    targeting_insights['total_target_queries'] += 1
                elif query_type == 'contact':
                    targeting_insights['contact_requests'] += 1
                    targeting_insights['total_target_queries'] += 1
                elif query_type == 'facilities':
                    targeting_insights['facilities_interest'] += 1
                    targeting_insights['total_target_queries'] += 1
                elif query_type == 'faculty':
                    targeting_insights['faculty_inquiry'] += 1
                    targeting_insights['total_target_queries'] += 1
            
            # Get top visitor queries
            query_texts = [vq.query_text for vq in visitor_queries]
            top_queries = [item[0] for item in Counter(query_texts).most_common(5)]
            
            return {
                'total_queries': total_queries,
                'unique_visitors': unique_visitors,
                'targeting_insights': targeting_insights,
                'top_queries': top_queries,
                'excluded_telegram_users': True,
                'note': 'Visitors with Telegram ID mappings (verified students) are excluded from this analysis'
            }
            
        except Exception as e:
            current_app.logger.error(f"Error getting visitor queries analytics: {str(e)}")
            return {
                'total_queries': 0,
                'unique_visitors': 0,
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
