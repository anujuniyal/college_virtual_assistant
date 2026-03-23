#!/usr/bin/env python3
"""
Setup and populate database with sample data for College Virtual Assistant
"""
import os
import sys
from datetime import datetime, timedelta

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.extensions import db
from app.models import (
    Student, Faculty, Admin, Notification, Result, FeeRecord,
    Complaint, ChatbotQA, QueryLog, Session,
    DailyViewCount, StudentRegistration, TelegramUserMapping, VisitorQuery,
    PredefinedInfo, FAQ, FAQRecord, OTP
)
from werkzeug.security import generate_password_hash

def setup_database():
    """Create all database tables"""
    app = create_app()
    with app.app_context():
        print("🔧 Creating database tables...")
        
        # Drop all tables and recreate them to ensure proper schema
        db.drop_all()
        db.create_all()
        print("✅ Database tables created successfully!")

def populate_sample_data():
    """Populate database with sample data"""
    app = create_app()
    with app.app_context():
        print("📝 Populating database with sample data...")
        
        # Clear existing data
        db.session.query(VisitorQuery).delete()
        db.session.query(TelegramUserMapping).delete()
        db.session.query(DailyViewCount).delete()
        db.session.query(QueryLog).delete()
        db.session.query(FAQRecord).delete()
        db.session.query(FAQ).delete()
        db.session.query(ChatbotQA).delete()
        db.session.query(Complaint).delete()
        db.session.query(FeeRecord).delete()
        db.session.query(Result).delete()
        db.session.query(Notification).delete()
        db.session.query(Session).delete()
        db.session.query(StudentRegistration).delete()
        db.session.query(OTP).delete()
        db.session.query(PredefinedInfo).delete()
        db.session.query(Student).delete()
        db.session.query(Faculty).delete()
        db.session.query(Admin).delete()
        db.session.commit()
        
        # Create Admin users
        print("👤 Creating admin users...")
        admin1 = Admin(
            username='admin',
            email='admin@college.edu',
            password_hash=generate_password_hash('admin123'),
            role='admin'
        )
        admin2 = Admin(
            username='accounts',
            email='accounts@college.edu',
            password_hash=generate_password_hash('accounts123'),
            role='accounts'
        )
        admin3 = Admin(
            username='faculty_admin',
            email='faculty@college.edu',
            password_hash=generate_password_hash('faculty123'),
            role='faculty'
        )
        db.session.add_all([admin1, admin2, admin3])
        
        # Create Faculty members
        print("👨‍🏫 Creating faculty members...")
        faculty_data = [
            {
                'name': 'Dr. Rajesh Kumar',
                'email': 'rajesh.kumar@college.edu',
                'department': 'Computer Science',
                'consultation_time': 'Mon-Wed, 2:00-4:00 PM',
                'phone': '9876543210',
                'role': 'faculty'
            },
            {
                'name': 'Dr. Priya Sharma',
                'email': 'priya.sharma@college.edu',
                'department': 'Electronics',
                'consultation_time': 'Tue-Thu, 10:00-12:00 PM',
                'phone': '9876543211',
                'role': 'faculty'
            },
            {
                'name': 'Dr. Amit Patel',
                'email': 'amit.patel@college.edu',
                'department': 'Mechanical',
                'consultation_time': 'Wed-Fri, 3:00-5:00 PM',
                'phone': '9876543212',
                'role': 'faculty'
            },
            {
                'name': 'Dr. Sunita Reddy',
                'email': 'sunita.reddy@college.edu',
                'department': 'Civil',
                'consultation_time': 'Mon-Thu, 11:00-1:00 PM',
                'phone': '9876543213',
                'role': 'faculty'
            },
            {
                'name': 'Dr. Vikram Singh',
                'email': 'vikram.singh@college.edu',
                'department': 'Computer Science',
                'consultation_time': 'Tue-Fri, 1:00-3:00 PM',
                'phone': '9876543214',
                'role': 'faculty'
            }
        ]
        
        for faculty_info in faculty_data:
            faculty = Faculty(**faculty_info)
            faculty.set_password('faculty123')
            db.session.add(faculty)
        
        # Create Students
        print("🎓 Creating students...")
        student_data = [
            {
                'roll_number': 'EDU20240001',
                'name': 'Anuj Kumar',
                'phone': '9876543201',
                'email': 'anuj.kumar@college.edu',
                'department': 'Computer Science',
                'semester': 3
            },
            {
                'roll_number': 'EDU20240002',
                'name': 'Priya Singh',
                'phone': '9876543202',
                'email': 'priya.singh@college.edu',
                'department': 'Electronics',
                'semester': 3
            },
            {
                'roll_number': 'EDU20240003',
                'name': 'Rahul Sharma',
                'phone': '9876543203',
                'email': 'rahul.sharma@college.edu',
                'department': 'Mechanical',
                'semester': 5
            },
            {
                'roll_number': 'EDU20240004',
                'name': 'Neha Patel',
                'phone': '9876543204',
                'email': 'neha.patel@college.edu',
                'department': 'Civil',
                'semester': 5
            },
            {
                'roll_number': 'EDU20240005',
                'name': 'Amit Kumar',
                'phone': '9876543205',
                'email': 'amit.kumar@college.edu',
                'department': 'Computer Science',
                'semester': 7
            }
        ]
        
        for student_info in student_data:
            student = Student(**student_info)
            db.session.add(student)
        
        db.session.commit()
        
        # Create Fee Records
        print("💰 Creating fee records...")
        fee_data = [
            {'student_id': 1, 'semester': 3, 'total_amount': 150000, 'paid_amount': 75000},
            {'student_id': 2, 'semester': 3, 'total_amount': 140000, 'paid_amount': 70000},
            {'student_id': 3, 'semester': 5, 'total_amount': 130000, 'paid_amount': 130000},
            {'student_id': 4, 'semester': 5, 'total_amount': 120000, 'paid_amount': 60000},
            {'student_id': 5, 'semester': 7, 'total_amount': 150000, 'paid_amount': 150000},
        ]
        
        for fee_info in fee_data:
            fee_info['balance_amount'] = fee_info['total_amount'] - fee_info['paid_amount']
            fee_record = FeeRecord(**fee_info)
            db.session.add(fee_record)
        
        # Create Results
        print("📊 Creating results...")
        result_data = [
            {'student_id': 1, 'semester': 3, 'subject': 'Data Structures', 'marks': 85, 'grade': 'A', 'created_by': 3},
            {'student_id': 1, 'semester': 3, 'subject': 'Algorithms', 'marks': 78, 'grade': 'B', 'created_by': 3},
            {'student_id': 1, 'semester': 3, 'subject': 'Database Systems', 'marks': 92, 'grade': 'A+', 'created_by': 3},
            {'student_id': 2, 'semester': 3, 'subject': 'Digital Electronics', 'marks': 88, 'grade': 'A', 'created_by': 3},
            {'student_id': 2, 'semester': 3, 'subject': 'Microprocessors', 'marks': 76, 'grade': 'B', 'created_by': 3},
            {'student_id': 3, 'semester': 5, 'subject': 'Thermodynamics', 'marks': 82, 'grade': 'A', 'created_by': 3},
            {'student_id': 3, 'semester': 5, 'subject': 'Fluid Mechanics', 'marks': 79, 'grade': 'B', 'created_by': 3},
        ]
        
        for result_info in result_data:
            result = Result(**result_info)
            db.session.add(result)
        
        # Create Notifications
        print("📢 Creating notifications...")
        notification_data = [
            {
                'title': 'Mid-Semester Examination Schedule',
                'content': 'Mid-semester examinations will start from 15th March 2024. Please check your exam schedule from the student portal.',
                'notification_type': 'exam',
                'priority': 'high',
                'expires_at': datetime.utcnow() + timedelta(days=30),
                'created_by': 1
            },
            {
                'title': 'Fee Payment Deadline',
                'content': 'Last date for fee payment for current semester is 31st March 2024. Late fees will be charged after deadline.',
                'notification_type': 'fee',
                'priority': 'high',
                'expires_at': datetime.utcnow() + timedelta(days=20),
                'created_by': 2
            },
            {
                'title': 'Annual Sports Meet',
                'content': 'Annual sports meet will be organized on 5th-7th April 2024. Interested students should register with sports department.',
                'notification_type': 'event',
                'priority': 'medium',
                'expires_at': datetime.utcnow() + timedelta(days=45),
                'created_by': 1
            },
            {
                'title': 'Workshop on Machine Learning',
                'content': 'A 3-day workshop on Machine Learning will be conducted by Computer Science department from 20th March 2024.',
                'notification_type': 'academic',
                'priority': 'medium',
                'expires_at': datetime.utcnow() + timedelta(days=25),
                'created_by': 3
            }
        ]
        
        for notification_info in notification_data:
            notification = Notification(**notification_info)
            db.session.add(notification)
        
        # Create Chatbot Q&A
        print("🤖 Creating chatbot Q&A...")
        qa_data = [
            {
                'question': 'what is the admission process',
                'answer': 'The admission process involves: 1) Fill online application form, 2) Upload required documents, 3) Pay application fee, 4) Appear for counseling, 5) Document verification, 6) Fee payment.',
                'category': 'admission'
            },
            {
                'question': 'courses offered',
                'answer': 'We offer B.Tech (CSE, ECE, ME, CE), BBA, BCA, M.Tech, and MBA programs.',
                'category': 'course'
            },
            {
                'question': 'fee structure',
                'answer': 'B.Tech: ₹1,50,000/year, BBA: ₹80,000/year, BCA: ₹70,000/year, M.Tech: ₹1,00,000/year, MBA: ₹1,20,000/year',
                'category': 'fee'
            },
            {
                'question': 'hostel facilities',
                'answer': 'We provide separate hostels for boys and girls with AC/non-AC rooms, mess facilities, 24/7 security, and medical facilities.',
                'category': 'facilities'
            },
            {
                'question': 'library timings',
                'answer': 'Library is open from 8:00 AM to 8:00 PM on all working days and 9:00 AM to 5:00 PM on weekends.',
                'category': 'facilities'
            }
        ]
        
        for qa_info in qa_data:
            qa = ChatbotQA(**qa_info)
            db.session.add(qa)
        
        # Create sample visitor queries
        print("📋 Creating sample visitor queries...")
        visitor_query_data = [
            {
                'query_type': 'admission',
                'query_text': 'admission',
                'response_text': '📚 **ADMISSION PROCESS**\n\n📋 **Eligibility Criteria:**\n• Minimum 60% in 10+2 for UG courses...',
                'phone_number': None,
                'telegram_user_id': None
            },
            {
                'query_type': 'course',
                'query_text': 'courses',
                'response_text': '📖 **COURSES & FEE STRUCTURE**\n\n🎓 **UNDERGRADUATE PROGRAMS (4 Years):**...',
                'phone_number': None,
                'telegram_user_id': None
            },
            {
                'query_type': 'contact',
                'query_text': 'contact',
                'response_text': '📞 **COLLEGE CONTACT INFORMATION**\n\n🏢 **MAIN RECEPTION:**...',
                'phone_number': None,
                'telegram_user_id': None
            }
        ]
        
        for vq_info in visitor_query_data:
            vq = VisitorQuery(**vq_info)
            db.session.add(vq)
        
        db.session.commit()
        print("✅ Sample data populated successfully!")

def main():
    """Main function"""
    print("🚀 Setting up College Virtual Assistant Database...")
    
    try:
        setup_database()
        populate_sample_data()
        print("\n🎉 Database setup completed successfully!")
        print("\n📊 Sample Data Created:")
        print("• 3 Admin users")
        print("• 5 Faculty members")
        print("• 5 Students")
        print("• 5 Fee records")
        print("• 7 Results")
        print("• 4 Notifications")
        print("• 5 Chatbot Q&A")
        print("• 3 Sample visitor queries")
        print("\n🔐 Login Credentials:")
        print("• Admin: admin / admin123")
        print("• Accounts: accounts / accounts123")
        print("• Faculty: faculty / faculty123")
        print("\n📱 Sample Student Roll Numbers:")
        print("• EDU20240001 (Anuj Kumar - 9876543201)")
        print("• EDU20240002 (Priya Singh - 9876543202)")
        print("• EDU20240003 (Rahul Sharma - 9876543203)")
        
    except Exception as e:
        print(f"❌ Error setting up database: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
