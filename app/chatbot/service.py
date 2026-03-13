"""
WhatsApp Chatbot Service
"""
from flask import current_app
from datetime import datetime, date, timedelta
import re

from app.extensions import db
from app.models import (
    Student,
    Notification,
    Result,
    FeeRecord,
    Faculty,
    Complaint,
    ChatbotQA,
    ChatbotUnknown,
    QueryLog,
    Session,
    DailyViewCount,
)
from app.services.analytics_service import AnalyticsService
from app.config import Config


class ChatbotService:
    """Main chatbot service"""
    
    def __init__(self):
        self.visitor_mode_commands = {
            'hi': self._greet_visitor,
            'hello': self._greet_visitor,
            'help': self._show_help_visitor,
            'admission': self._admission_info,
            'course': self._course_info,
            'fee': self._fee_structure,
            'facilities': self._facilities_info,
            'faculty': self._faculty_list,
            # Numeric choices for all users
            '1': self._admission_info,
            '2': self._course_info,
            '3': self._fee_structure,
            '4': self._facilities_info,
            '5': self._faculty_list,
            '6': self._show_help_visitor,
        }
        
        self.student_mode_commands = {
            'hi': self._greet_student,
            'hello': self._greet_student,
            'help': self._show_help_student,
            'notice': self._get_notices,
            'notices': self._get_notices,
            'result': self._get_result,
            'results': self._get_result,
            'fee': self._get_fee_status,
            'fees': self._get_fee_status,
            'faculty': self._search_faculty,
            'logout': self._logout_student,
            # Numeric choices
            '1': self._get_result,
            '2': self._get_notices,
            '3': self._get_fee_status,
            '4': self._search_faculty,
            '5': self._complaint_instructions,
            '6': self._logout_student,
        }
    
    def process_message(self, message: str, phone_number: str) -> str:
        """Process incoming WhatsApp message"""
        message_lower = message.lower().strip()
        
        # Check if user is registered student
        session_obj = Session.query.filter_by(phone_number=phone_number).first()
        
        if session_obj and session_obj.verified:
            # Student mode
            return self._handle_student_mode(message_lower, phone_number, session_obj.student_id)
        else:
            # Visitor mode or registration - pass original message for roll number extraction
            return self._handle_visitor_mode(message, phone_number)
    
    def _handle_visitor_mode(self, message: str, phone_number: str) -> str:
        """Handle visitor mode messages"""
        normalized = message.strip()
        message_lower = normalized.lower()

        # Check for registration (case-insensitive)
        if message_lower.startswith('register') or message_lower.startswith('verify'):
            return self._handle_registration(normalized, phone_number)
        
        # Check for roll number verification
        roll_match = re.search(r'roll[:\s]*([A-Z0-9]+)', normalized, re.IGNORECASE)
        if roll_match:
            roll_number = roll_match.group(1).upper()
            return self._verify_student(roll_number, phone_number)
        
        # Handle commands
        for cmd, handler in self.visitor_mode_commands.items():
            if message_lower.startswith(cmd):
                return handler(phone_number)
        
        # Try Q&A lookup
        answer = self._lookup_qa(message)
        if answer:
            return answer
        
        # Store unknown query
        self._store_unknown_query(message, phone_number)
        return "I'm sorry, I didn't understand that. Please type 'help' to see available options."
    
    def _handle_student_mode(self, message: str, phone_number: str, student_id: int) -> str:
        """Handle registered student messages"""
        # Check for complaint first (special handling)
        if message.startswith('complaint'):
            return self._register_complaint(message, phone_number, student_id)
        
        # Handle commands
        for cmd, handler in self.student_mode_commands.items():
            if message.startswith(cmd):
                return handler(phone_number, student_id)
        
        # Try Q&A lookup
        answer = self._lookup_qa(message)
        if answer:
            return answer
        
        # Store unknown query
        self._store_unknown_query(message, phone_number, student_id)
        return "I'm sorry, I didn't understand that. Type 'help' to see available options."
    
    def _handle_registration(self, message: str, phone_number: str) -> str:
        """Handle student registration via roll number as pass key"""
        # Extract roll number from message - handle both "register" and "verify" patterns
        roll_match = re.search(r'(?:register|verify)\s+([A-Z0-9]+)', message, re.IGNORECASE)
        if not roll_match:
            roll_match = re.search(r'roll[:\s]*([A-Z0-9]+)', message, re.IGNORECASE)
        
        if roll_match:
            roll_number = roll_match.group(1).upper()
            return self._verify_student_by_roll_and_phone(roll_number, phone_number)
        
        return "Please provide your roll number in format: 'register EDU20240051' or 'verify EDU20240051'"
    
    def _get_or_create_view_count(self, student_id: int, service_type: str) -> DailyViewCount:
        """Get or create daily view count record"""
        today = date.today()
        
        view_count = DailyViewCount.query.filter_by(
            student_id=student_id,
            service_type=service_type,
            view_date=today
        ).first()
        
        if not view_count:
            view_count = DailyViewCount(
                student_id=student_id,
                service_type=service_type,
                view_date=today,
                view_count=0
            )
            db.session.add(view_count)
            db.session.commit()
        
        return view_count
    
    def _get_view_counts_status(self, student_id: int) -> str:
        """Get formatted view counts status for student"""
        result_count = self._get_or_create_view_count(student_id, 'result')
        fee_count = self._get_or_create_view_count(student_id, 'fee')
        
        max_result = int(getattr(Config, 'RATE_LIMIT_RESULT_QUERIES', 1) or 1)
        max_fee = int(getattr(Config, 'RATE_LIMIT_FEE_QUERIES', 1) or 1)

        result_remaining = result_count.get_remaining_views(max_daily_views=max_result)
        fee_remaining = fee_count.get_remaining_views(max_daily_views=max_fee)
        
        status = f"\n📊 **Daily View Limits:**\n"
        status += f"📋 Results: {result_remaining}/{max_result} left today\n"
        status += f"💰 Fee Status: {fee_remaining}/{max_fee} left today"
        
        return status
    
    def _verify_student_by_roll_and_phone(self, roll_number: str, telegram_phone: str) -> str:
        """Verify student by roll number (pass key) and match phone numbers"""
        # Extract phone number from telegram_phone (remove whatsapp:+ prefix)
        user_phone = telegram_phone.replace('whatsapp:+', '')
        
        # Find student by roll number
        student = Student.query.filter_by(roll_number=roll_number).first()
        
        if not student:
            return f"Roll number {roll_number} not found in student records. Please contact admin."
        
        # Check if phone numbers match
        if student.phone != user_phone:
            return f"❌ Verification Failed!\n\nThe phone number you're using ({user_phone}) doesn't match the registered phone number for roll number {roll_number}.\n\nRegistered phone: {student.phone}\n\nPlease contact admin if you need to update your phone number."
        
        # Create or update session
        session_obj = Session.query.filter_by(phone_number=telegram_phone).first()
        if not session_obj:
            session_obj = Session(phone_number=telegram_phone, student_id=student.id)
            db.session.add(session_obj)
        else:
            session_obj.student_id = student.id
        
        session_obj.verified = True
        session_obj.last_activity = datetime.utcnow()
        db.session.commit()
        
        # Get view counts status
        view_status = self._get_view_counts_status(student.id)
        
        return f"""✅ Verification Successful!

🎓 Welcome {student.name}!

📚 **Your Details:**
• Roll No: {roll_number}
• Department: {student.department}
• Semester: {student.semester}
• Phone: {student.phone}

🚀 **Available Services:**

📋 **Academic:**
1️⃣ Results - View your academic results
2️⃣ Notices - Check latest notifications

💰 **Fee:**
3️⃣ Fee Status - Check your fee status

👨‍🏫 **Support:**
4️⃣ Faculty - Search faculty information
5️⃣ Complaint - File a complaint

📱 **Account:**
6️⃣ Logout - End your session

{view_status}

Simply type the number (1-6) to choose any service!"""
    
    def _verify_student_by_phone(self, student_phone: str, telegram_phone: str) -> str:
        """Verify student by phone number and create session"""
        student = Student.query.filter_by(phone=student_phone).first()
        
        if not student:
            return f"Phone number {student_phone} not found in student records. Please contact admin."
        
        # Create or update session
        session_obj = Session.query.filter_by(phone_number=telegram_phone).first()
        if not session_obj:
            session_obj = Session(phone_number=telegram_phone, student_id=student.id)
            db.session.add(session_obj)
        else:
            session_obj.student_id = student.id
        
        session_obj.verified = True
        session_obj.last_activity = datetime.utcnow()
        db.session.commit()
        
        return f"✅ Verified! Welcome {student.name}.\n\n📚 Student Details:\n• Roll No: {student.roll_number}\n• Department: {student.department}\n• Semester: {student.semester}\n\nYou can now access:\n• Notices\n• Results\n• Fee Status\n• Faculty Info\n• File Complaints\n\nType 'help' for commands."
    
    def _verify_student(self, roll_number: str, phone_number: str) -> str:
        """Verify student and create session"""
        # Extract phone number from telegram_phone (remove whatsapp:+ prefix)
        user_phone = phone_number.replace('whatsapp:+', '')
        
        student = Student.query.filter_by(roll_number=roll_number).first()
        
        if not student:
            return f"Roll number {roll_number} not found. Please contact admin."
        
        # Check if phone matches
        if student.phone != user_phone:
            return f"Phone number does not match records for roll number {roll_number}. Please contact admin."
        
        # Create or update session
        session_obj = Session.query.filter_by(phone_number=phone_number).first()
        if not session_obj:
            session_obj = Session(phone_number=phone_number, student_id=student.id)
            db.session.add(session_obj)
        else:
            session_obj.student_id = student.id
        
        session_obj.verified = True
        session_obj.last_activity = datetime.utcnow()
        db.session.commit()
        
        # Get view counts status
        view_status = self._get_view_counts_status(student.id)
        
        return f"""✅ Verified! Welcome {student.name}.

📚 Student Details:
• Roll No: {roll_number}
• Department: {student.department}
• Semester: {student.semester}

You can now access:
• Notices
• Results
• Fee Status
• Faculty Info
• File Complaints

Type 'help' for commands."""
    
    def _greet_visitor(self, phone_number: str) -> str:
        """Greet visitor"""
        return """👋 Welcome to College Virtual Assistant!

📋 **Available Services (Visitor Mode):**

📌 **General Information:**
1️⃣ Admission - Admission FAQs
2️⃣ Courses - Course details

💰 **Fees:**
3️⃣ Fee Structure - Course fee structure

🏫 **Campus:**
4️⃣ Facilities - College facilities
5️⃣ Faculty - Faculty information

ℹ️ **Help:**
6️⃣ Help - Show this menu

Simply type the number (1-6) to choose any service.

To unlock student services, verify with your roll number:
Type: register EDU20240051"""
    
    def _greet_student(self, phone_number: str, student_id: int) -> str:
        """Greet registered student and show available services"""
        student = Student.query.get(student_id)
        name = student.name if student else "Student"
        
        # Get view counts status
        view_status = self._get_view_counts_status(student_id)
        
        return f"""👋 Hello {name}! Welcome back!

📚 **Available Services:**

📋 **Academic Services:**
1️⃣ Results - View your academic results
2️⃣ Notices - Check latest notifications

💰 **Fee Services:**
3️⃣ Fee Status - Check your fee status and payment details

👨‍🏫 **Faculty & Support:**
4️⃣ Faculty - Search faculty information
5️⃣ Complaint - File a complaint

📱 **Account:**
6️⃣ Logout - End your session

{view_status}

Simply type the number (1-6) to choose any service!"""
    
    def _show_help_visitor(self, phone_number: str) -> str:
        """Show help for visitors"""
        return """📋 **Available Services (Visitor Mode):**

📌 **General Information:**
1️⃣ Admission - Admission FAQs
2️⃣ Courses - Course details

💰 **Fees:**
3️⃣ Fee Structure - Course fee structure

🏫 **Campus:**
4️⃣ Facilities - College facilities
5️⃣ Faculty - Faculty information

ℹ️ **Help:**
6️⃣ Help - Show this menu

Simply type the number (1-6) to choose any service.

To unlock student services, verify with your roll number:
Type: register EDU20240051"""
    
    def _show_help_student(self, phone_number: str, student_id: int) -> str:
        """Show help for students"""
        view_status = self._get_view_counts_status(student_id)

        return f"""📋 **Available Services (Student Mode):**

📋 **Academic:**
1️⃣ Results - View your academic results
2️⃣ Notices - Check latest notifications

💰 **Fee:**
3️⃣ Fee Status - Check your fee status

👨‍🏫 **Support:**
4️⃣ Faculty - Search faculty information
5️⃣ Complaint - File a complaint

📱 **Account:**
6️⃣ Logout - End your session

{view_status}

Simply type the number (1-6) to choose any service!"""

    def _complaint_instructions(self, phone_number: str, student_id: int) -> str:
        """Show complaint instructions for numeric shortcut"""
        return """📝 Complaint Registration

To file a complaint, type:
complaint <your message>

Example:
complaint Ragging incident in hostel"""
    
    def _admission_info(self, phone_number: str) -> str:
        """Admission information"""
        return """📚 ADMISSION INFORMATION

• Application forms available online
• Last date: Check college website
• Required documents: 10th, 12th marksheets, ID proof
• Entrance exam: As per university guidelines

For detailed information, visit: www.college.edu/admission

Issued by: College Admin"""
    
    def _course_info(self, phone_number: str) -> str:
        """Course information"""
        return """📖 COURSE DETAILS

Available Courses:
• B.Tech (CSE, ECE, ME, CE)
• BBA
• BCA
• M.Tech
• MBA

Duration: 4 years (UG), 2 years (PG)
Eligibility: 12th pass with minimum 60%

For detailed syllabus, visit: www.college.edu/courses

Issued by: College Admin"""
    
    def _fee_structure(self, phone_number: str) -> str:
        """General fee structure"""
        return """💰 FEE STRUCTURE (General)

B.Tech: ₹1,50,000/year
BBA: ₹80,000/year
BCA: ₹70,000/year
M.Tech: ₹1,00,000/year
MBA: ₹1,20,000/year

*Includes tuition, library, lab fees
*Hostel fees separate

For detailed breakdown, verify your roll number and check 'fee' command.

Issued by: Accounts Section"""
    
    def _facilities_info(self, phone_number: str) -> str:
        """Facilities information"""
        return """🏫 COLLEGE FACILITIES

• Library with 50,000+ books
• Computer Labs (24/7)
• Sports Complex
• Hostel (Boys & Girls)
• Cafeteria
• Medical Center
• Wi-Fi Campus
• Auditorium

For more details, visit: www.college.edu/facilities

Issued by: College Admin"""
    
    def _faculty_list(self, phone_number: str) -> str:
        """Get faculty list"""
        faculty_list = Faculty.query.limit(10).all()
        
        if not faculty_list:
            return "No faculty information available."
        
        response = "👨‍🏫 FACULTY LIST\n\n"
        for faculty in faculty_list:
            response += f"• {faculty.name}\n  Dept: {faculty.department}\n  Email: {faculty.email}\n\n"
        
        response += "To search specific faculty, verify your roll number and use 'faculty NAME' command."
        return response
    
    def _get_notices(self, phone_number: str, student_id: int) -> str:
        """Get active notices"""
        notices = Notification.query.filter(
            Notification.expires_at > datetime.utcnow()
        ).order_by(Notification.created_at.desc()).limit(8).all()
        
        if not notices:
            return "No active notices at the moment."
        
        response = "📢 LATEST NOTICES\n\n"
        for notice in notices:
            response += f"📌 {notice.title}\n{notice.content}\n"
            if notice.link_url:
                response += f"Link: {notice.link_url}\n"
            response += f"Date: {notice.created_at.strftime('%d-%m-%Y')}\n\n"
        
        response += "Issued by: College Admin"
        return response
    
    def _get_result(self, phone_number: str, student_id: int) -> str:
        """Get student results"""
        # Check daily view limit
        view_count = self._get_or_create_view_count(student_id, 'result')
        
        max_daily = int(getattr(Config, 'RATE_LIMIT_RESULT_QUERIES', 1) or 1)
        if not view_count.can_view(max_daily_views=max_daily):
            remaining = view_count.get_remaining_views(max_daily_views=max_daily)
            return f"⏰ You have reached your daily limit for viewing results.\n\n📊 **Daily View Status:**\n📋 Results: {remaining}/{max_daily} left today\n\nYou can check results again tomorrow!"
        
        # Get student
        student = Student.query.get(student_id)
        if not student:
            return "Student record not found."
        
        # Get latest results
        results = Result.query.filter_by(student_id=student_id).filter(
            Result.declared_at >= datetime.utcnow() - timedelta(days=Config.RESULT_VISIBILITY_DAYS)
        ).order_by(Result.declared_at.desc()).all()
        
        if not results:
            return "No results available at the moment."
        
        # Increment view count
        view_count.increment_view()
        
        # Format results
        response = f"📊 **ACADEMIC RESULTS - {student.name}**\n"
        response += f"🆔 Roll No: {student.roll_number}\n"
        response += f"📚 Semester: {student.semester}\n\n"
        
        for result in results:
            response += f"📋 {result.subject}: {result.marks}/100 ({result.grade})\n"
        
        remaining_views = view_count.get_remaining_views(max_daily_views=max_daily)
        response += f"\n📊 **Daily View Status:**\n📋 Results: {remaining_views}/{max_daily} left today"

        # Tag issuer if available
        try:
            issuer_id = results[0].created_by
            if issuer_id:
                from app.models import Admin
                issuer = Admin.query.get(int(issuer_id))
                if issuer:
                    response += f"\n\nIssued by: {issuer.username}"
        except Exception:
            pass
        
        return response
    
    def _get_fee_status(self, phone_number: str, student_id: int) -> str:
        """Get fee status"""
        # Check daily view limit
        view_count = self._get_or_create_view_count(student_id, 'fee')
        
        max_daily = int(getattr(Config, 'RATE_LIMIT_FEE_QUERIES', 1) or 1)
        if not view_count.can_view(max_daily_views=max_daily):
            remaining = view_count.get_remaining_views(max_daily_views=max_daily)
            return f"⏰ You have reached your daily limit for viewing fee status.\n\n📊 **Daily View Status:**\n💰 Fee Status: {remaining}/{max_daily} left today\n\nYou can check fee status again tomorrow!"
        
        # Get latest fee record
        fee_record = FeeRecord.query.filter_by(student_id=student_id).order_by(
            FeeRecord.last_updated.desc()
        ).first()
        
        if not fee_record:
            return "Fee record not found. Please contact accounts section."
        
        # Increment view count
        view_count.increment_view()
        
        # Format response
        student = Student.query.get(student_id)
        response = f"💰 FEE STATUS - {student.roll_number}\n\n"
        response += f"Semester: {fee_record.semester}\n"
        response += f"Total Amount: ₹{fee_record.total_amount:,.2f}\n"
        response += f"Paid Amount: ₹{fee_record.paid_amount:,.2f}\n"
        response += f"Balance: ₹{fee_record.balance:,.2f}\n\n"
        response += f"Last Updated: {fee_record.last_updated.strftime('%d-%m-%Y')}\n"
        
        remaining_views = view_count.get_remaining_views(max_daily_views=max_daily)
        response += f"\n📊 **Daily View Status:**\n💰 Fee Status: {remaining_views}/{max_daily} left today"
        response += "\n\nGenerated by: Accounts Section"
        
        return response
    
    def _search_faculty(self, phone_number: str, student_id: int) -> str:
        """Search faculty"""
        # This would be called with a name parameter
        # For now, return full list
        faculty_list = Faculty.query.limit(20).all()
        
        if not faculty_list:
            return "No faculty information available."
        
        response = "👨‍🏫 FACULTY INFORMATION\n\n"
        for faculty in faculty_list:
            response += f"• {faculty.name}\n"
            response += f"  Department: {faculty.department}\n"
            response += f"  Email: {faculty.email}\n"
            if faculty.consultation_time:
                response += f"  Consultation: {faculty.consultation_time}\n"
            response += "\n"
        
        return response
    
    def _logout_student(self, phone_number: str, student_id: int) -> str:
        """Logout student and end session"""
        # Find and delete session
        session_obj = Session.query.filter_by(phone_number=phone_number).first()
        if session_obj:
            db.session.delete(session_obj)
            db.session.commit()
        
        return """👋 Logged out successfully!

Your session has been ended for security.

To access services again:
• Verify your roll number: register EDU20240051

Thank you for using College Virtual Assistant!"""
    
    def _register_complaint(self, message: str, phone_number: str, student_id: int) -> str:
        """Register complaint"""
        # Parse complaint from message
        parts = message.split(' ', 2)
        
        if len(parts) < 3:
            return """🚨 ANTI-RAGGING COMPLAINT

To file a complaint, please provide:
Format: complaint CATEGORY DESCRIPTION

Example: complaint ragging I faced ragging in hostel room 205

Categories: ragging, harassment, other

Your complaint will be registered with your roll number."""
        
        category = parts[1].lower()
        description = parts[2] if len(parts) > 2 else ''
        
        if category not in ['ragging', 'harassment', 'other']:
            return f"Invalid category. Use: ragging, harassment, or other"
        
        if not description or len(description) < 10:
            return "Please provide a detailed description (at least 10 characters)."
        
        # Create complaint
        complaint = Complaint(
            student_id=student_id,
            category=category,
            description=description,
            status='pending'
        )
        db.session.add(complaint)
        db.session.commit()
        
        return f"✅ Complaint registered successfully!\n\nCategory: {category}\nComplaint ID: {complaint.id}\n\nYour complaint will be reviewed by the administration."
    
    def _lookup_qa(self, message: str) -> str:
        """Lookup Q&A from database"""
        # Simple keyword matching
        qa = ChatbotQA.query.filter(
            ChatbotQA.question.ilike(f'%{message}%')
        ).first()
        
        if qa:
            return qa.answer
        
        return None
    
    def _store_unknown_query(self, message: str, phone_number: str, student_id: int = None):
        """Store unknown query"""
        unknown = ChatbotUnknown(
            query=message,
            phone_number=phone_number,
            student_id=student_id
        )
        db.session.add(unknown)
        db.session.commit()
        
        # Track analytics
        AnalyticsService.track_query()
