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
    FAQRecord,
    QueryLog,
    Session,
    DailyViewCount,
    VisitorQuery,
)
from app.services.analytics_service import AnalyticsService
from app.services.complaint_notification_service import ComplaintNotificationService
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
            'courses': self._course_info,
            'fee': self._fee_structure,
            'fees': self._fee_structure,
            'facilities': self._facilities_info,
            'faculty': self._faculty_list,
            'contact': self._contact_info,
            'reception': self._contact_info,
            'phone': self._contact_info,
            # Numeric choices for all users
            '1': self._admission_info,
            '2': self._course_info,
            '3': self._faculty_list,
            '4': self._facilities_info,
            '5': self._contact_info,
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

        # Check for roll number verification (direct roll number input)
        roll_match = re.search(r'EDU\d{5}', normalized, re.IGNORECASE)
        if roll_match:
            roll_number = roll_match.group(0).upper()
            return self._verify_student(roll_number, phone_number)
        
        # Handle commands
        for cmd, handler in self.visitor_mode_commands.items():
            if message_lower.startswith(cmd):
                response = handler(phone_number)
                # Store visitor query
                self._store_visitor_query(message, response, phone_number, cmd)
                return response
        
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
        # Extract roll number from message - direct roll number pattern
        roll_match = re.search(r'EDU\d{5}', message, re.IGNORECASE)
        if roll_match:
            roll_number = roll_match.group(0).upper()
            return self._verify_student_by_roll_and_phone(roll_number, phone_number)
        
        return "Please provide your roll number in format: EDU25001"
    
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
            return f"❌ Roll number {roll_number} not found in student records.\n\n📋 Available options:\n• Check your roll number spelling\n• Contact admin if roll number is incorrect\n\n📞 Admin: admin@edubot.com"
        
        # Log verification attempt for debugging
        from flask import current_app
        current_app.logger.info(f"Roll verification attempt: {roll_number} -> {student.name}")
        current_app.logger.info(f"Phone comparison: {user_phone} vs {student.phone}")
        
        # Check if phone numbers match
        if student.phone != user_phone:
            return f"""❌ Verification Failed!

🔍 **Mismatch Details:**
• Roll Number: {roll_number}
• Student Name: {student.name}
• Phone you're using: {user_phone}
• Registered phone: {student.phone}

📋 **Possible Solutions:**
1. Use the registered phone number: {student.phone}
2. Contact admin to update your phone number
3. Re-check the phone number you shared

📞 Need help? Contact admin: admin@edubot.com"""
        
        # Create or update session
        session_obj = Session.query.filter_by(phone_number=telegram_phone).first()
        if not session_obj:
            session_obj = Session(phone_number=telegram_phone, student_id=student.id)
            db.session.add(session_obj)
        else:
            session_obj.student_id = student.id
        
        session_obj.verified = True
        session_obj.last_activity = datetime.utcnow()
        
        # Link Telegram account to student record if this is a Telegram user
        if telegram_phone.startswith('whatsapp:+visitor_'):
            # Extract Telegram user ID from visitor phone number
            telegram_user_id = telegram_phone.replace('whatsapp:+visitor_', '')
            try:
                success, message = student.link_telegram_account(telegram_user_id)
                if success:
                    current_app.logger.info(f"Successfully linked Telegram account for student {student.name} ({student.roll_number})")
                else:
                    current_app.logger.warning(f"Failed to link Telegram account: {message}")
            except Exception as e:
                current_app.logger.error(f"Error linking Telegram account: {str(e)}")
        
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
1. Results - View your academic results
2. Notices - Check latest notifications

💰 **Fee:**
3. Fee Status - Check your fee status

👨‍🏫 **Support:**
4. Faculty - Search faculty information
5. Complaint - File a complaint

📱 **Account:**
6. Logout - End your session

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
        return """🏫 **Welcome to College Virtual Assistant!**

📋 **Visitor Service Mode**

📌 **General Information:**
1. Admission Process - Admission requirements and procedure
2. Courses & Fees - Available courses and fee structure
3. Faculty Details - Faculty directory and information
4. Facilities - Campus facilities and infrastructure
5. Contact Info - Reception and contact details
6. Help - Show this menu

📞 **Reception Contact:**
📱 Phone: +91-12345-67890
📧 Email: info@college.edu
🕐 Office Hours: 9:00 AM - 5:00 PM

🎓 **Students:** To access personalized services,
Type: `EDU25001`
or
Share your phone number using the button below
📱 [Share Phone Number]

Simply type a number (1-6) or keyword to get started!"""
    
    def _greet_student(self, phone_number: str, student_id: int) -> str:
        """Greet registered student and show available services"""
        student = Student.query.get(student_id)
        name = student.name if student else "Student"
        
        # Get view counts status
        view_status = self._get_view_counts_status(student_id)
        
        return f"""Hello {name}! Welcome back!

**Available Services:**

**Academic Services:**
1. Results - View your academic results
2. Notices - Check latest notifications

**Fee Services:**
3. Fee Status - Check your fee status and payment details

**Faculty & Support:**
4. Faculty - Search faculty information
5. Complaint - File a complaint

**Account:**
6. Logout - End your session

{view_status}

Simply type the number (1-6) to choose any service!"""
    
    def _show_help_visitor(self, phone_number: str) -> str:
        """Show help for visitors"""
        return """**Available Services (Visitor Mode)**

**General Information:**
1. Admission Process - Admission requirements and procedure
2. Courses & Fees - Available courses and fee structure
3. Faculty Details - Faculty directory and information
4. Facilities - Campus facilities and infrastructure
5. Contact Info - Reception and contact details
6. Help - Show this menu

**Reception Contact:**
Phone: +91-12345-67890
Email: info@college.edu
Office Hours: 9:00 AM - 5:00 PM

**Students:** To access personalized services,
Type: `EDU25001`

Simply type a number (1-6) or keyword to get started!"""
    
    def _show_help_student(self, phone_number: str, student_id: int) -> str:
        """Show help for students"""
        view_status = self._get_view_counts_status(student_id)

        return f"""📋 **Available Services (Student Mode):**

📋 **Academic:**
1. Results - View your academic results
2. Notices - Check latest notifications

💰 **Fee:**
3. Fee Status - Check your fee status

👨‍🏫 **Support:**
4. Faculty - Search faculty information
5. Complaint - File a complaint

📱 **Account:**
6. Logout - End your session

{view_status}

Simply type the number (1-6) to choose any service!"""

    def _complaint_instructions(self, phone_number: str, student_id: int) -> str:
        """Show complaint format and allow direct complaint submission"""
        return """📝 **Complaint Registration**

**🔹 Option 1: File Complaint Now**
Send your complaint immediately in this format:
`complaint [category] [description]`

**📋 Available Categories:**
• `ragging` - Anti-ragging complaints
• `harassment` - Harassment issues  
• `other` - Other complaints

**📝 Example:**
`complaint ragging I faced ragging in hostel room 205`

**🔹 Option 2: Get Help**
Type `help` to see all available options

---
⚡ **Quick Response:** Your complaint will be immediately registered and admin will be notified!

📞 **For urgent matters:** Contact admin office directly"""
    
    def _admission_info(self, phone_number: str) -> str:
        """Admission information"""
        return """📚 **ADMISSION PROCESS**

📋 **Eligibility Criteria:**
• Minimum 60% in 10+2 for UG courses
• Valid score in entrance exam (JEE/CET/etc.)
• Age limit: As per university norms

📝 **Application Process:**
1. Fill online application form
2. Upload required documents
3. Pay application fee (₹500)
4. Appear for counseling/interview
5. Document verification
6. Fee payment and admission confirmation

📄 **Required Documents:**
• 10th and 12th mark sheets
• Transfer certificate
• Character certificate
• Passport size photographs (4)
• ID proof (Aadhar/Voter ID)
• Entrance exam scorecard

⏰ **Important Dates:**
• Application start: 1st May 2024
• Application deadline: 30th June 2024
• Merit list announcement: 15th July 2024
• Counseling starts: 20th July 2024

💰 **Application Fee:**
• General: ₹500
• SC/ST: ₹250

📞 **For Queries:**
Admission Cell: +91-12345-67891
Email: admission@college.edu

📍 **Admission Office:**
College Campus, Room No. 101
Office Hours: 9:00 AM - 5:00 PM

Issued by: Admission Department"""
    
    def _course_info(self, phone_number: str) -> str:
        """Course information with fees"""
        return """📖 **COURSES & FEE STRUCTURE**

🎓 **UNDERGRADUATE PROGRAMS (4 Years):**

**B.Tech Programs:**
• Computer Science & Engineering (CSE)
  📚 Seats: 120 | 💰 Fee: ₹1,50,000/year
• Electronics & Communication (ECE)
  📚 Seats: 90 | 💰 Fee: ₹1,40,000/year
• Mechanical Engineering (ME)
  📚 Seats: 120 | 💰 Fee: ₹1,30,000/year
• Civil Engineering (CE)
  📚 Seats: 60 | 💰 Fee: ₹1,20,000/year

**BBA (Bachelor of Business Administration):**
📚 Seats: 180 | 💰 Fee: ₹80,000/year

**BCA (Bachelor of Computer Applications):**
📚 Seats: 120 | 💰 Fee: ₹70,000/year

🎓 **POSTGRADUATE PROGRAMS (2 Years):**

**M.Tech Programs:**
• Computer Science Engineering
  📚 Seats: 18 | 💰 Fee: ₹1,00,000/year
• VLSI Design
  📚 Seats: 18 | 💰 Fee: ₹90,000/year

**MBA (Master of Business Administration):**
📚 Seats: 120 | 💰 Fee: ₹1,20,000/year

💰 **FEE STRUCTURE INCLUDES:**
• Tuition fees
• Library charges
• Laboratory fees
• Sports facilities
• Medical facilities
• Wi-Fi campus access

🏠 **HOSTEL FEES (Separate):**
• AC Room: ₹90,000/year
• Non-AC Room: ₹60,000/year
• Mess charges: ₹48,000/year

📝 **ELIGIBILITY:**
• UG: 60% in 10+2 with PCM/PCB
• PG: 60% in graduation + valid entrance score

📞 **For Course Details:**
Academic Office: +91-12345-67892
Email: academics@college.edu

Issued by: Academic Department"""
    
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
        """Get faculty list with details"""
        faculty_list = Faculty.query.limit(15).all()
        
        if not faculty_list:
            return "No faculty information available."
        
        response = "👨‍🏫 **FACULTY DIRECTORY**\n\n"
        for faculty in faculty_list:
            response += f"📝 **{faculty.name}**\n"
            response += f"🏢 Department: {faculty.department}\n"
            response += f"📧 Email: {faculty.email}\n"
            if faculty.consultation_time:
                response += f"🕐 Consultation: {faculty.consultation_time}\n"
            if faculty.phone:
                response += f"📱 Phone: {faculty.phone}\n"
            response += "\n"
        
        response += "📞 **Faculty Office:**\n"
        response += "📱 Phone: +91-12345-67893\n"
        response += "📧 Email: faculty@college.edu\n\n"
        response += "📍 For detailed faculty profiles, visit:\n"
        response += "www.college.edu/faculty\n\n"
        response += "To search specific faculty, verify your roll number and use 'faculty NAME' command.\n\n"
        response += "Issued by: Academic Department"
        return response
    
    def _contact_info(self, phone_number: str) -> str:
        """Contact information and reception details"""
        return """📞 **COLLEGE CONTACT INFORMATION**

🏢 **MAIN RECEPTION:**
📱 Phone: +91-12345-67890
📧 Email: info@college.edu
🕐 Office Hours: 9:00 AM - 5:00 PM (Mon-Sat)
📍 Location: Main Building, Ground Floor

📚 **ACADEMIC OFFICE:**
📱 Phone: +91-12345-67892
📧 Email: academics@college.edu
🕐 Office Hours: 10:00 AM - 4:00 PM
📍 Location: Academic Block, Room 201

💰 **ACCOUNTS SECTION:**
📱 Phone: +91-12345-67894
📧 Email: accounts@college.edu
🕐 Office Hours: 10:00 AM - 3:00 PM
📍 Location: Admin Block, Room 105

📝 **ADMISSION CELL:**
📱 Phone: +91-12345-67891
📧 Email: admission@college.edu
🕐 Office Hours: 9:00 AM - 5:00 PM
📍 Location: Admission Office, Room 101

🏥 **MEDICAL CENTER:**
📱 Phone: +91-12345-67895
📧 Email: medical@college.edu
🕐 Available: 24/7 Emergency
📍 Location: Campus Hospital

🏠 **HOSTEL OFFICE:**
📱 Phone: +91-12345-67896
📧 Email: hostel@college.edu
🕐 Office Hours: 8:00 AM - 8:00 PM
📍 Location: Hostel Block, Office Room

🚌 **TRANSPORT OFFICE:**
📱 Phone: +91-12345-67897
📧 Email: transport@college.edu
🕐 Office Hours: 8:00 AM - 6:00 PM
📍 Location: Transport Department

📧 **GENERAL EMAILS:**
• Information: info@college.edu
• Admissions: admission@college.edu
• Academics: academics@college.edu
• Complaints: complaints@college.edu
• Alumni: alumni@college.edu

🌐 **WEBSITE:**
www.college.edu

📍 **CAMPUS ADDRESS:**
College Campus,
Main Road,
City - 123456,
State, India

🗺️ **DIRECTIONS:**
• Nearest Railway Station: 5 km
• Nearest Airport: 15 km
• City Bus Stop: 500 meters

For any queries, feel free to contact the respective departments during office hours.

Issued by: College Administration"""
    
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
• Verify your roll number: EDU25001

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
        
        # Get student information
        student = Student.query.get(student_id)
        if not student:
            return "Student information not found. Please contact admin."
        
        # Create complaint
        complaint = Complaint(
            student_id=student_id,
            category=category,
            description=description,
            status='pending'
        )
        db.session.add(complaint)
        db.session.commit()
        
        # Send notification to admin/HOD
        try:
            notification_sent = ComplaintNotificationService.notify_admin_hod(
                complaint_id=complaint.id,
                category=category,
                description=description,
                student_name=student.name,
                roll_number=student.roll_number
            )
            
            if notification_sent:
                notification_msg = "\n📢 **✅ Admin/HOD has been notified and will review your complaint shortly!**"
            else:
                notification_msg = "\n⚠️ **❌ There was an issue notifying admin. Please contact the office directly.**"
        except Exception as e:
            current_app.logger.error(f"Error sending complaint notification: {str(e)}")
            notification_msg = "\n⚠️ **❌ There was an issue notifying admin. Please contact the office directly.**"
        
        return f"""✅ **Complaint Registered Successfully!**

📋 **Complaint Details:**
🆔 Complaint ID: {complaint.id}
👤 Student: {student.name} ({student.roll_number})
🏷️ Category: {category.upper()}
📝 Description: {description}

{notification_msg}

📫 **What happens next:**
• Admin will review your complaint within 24 hours
• You'll receive updates on action taken
• For urgent matters: Contact admin office immediately

📞 **Contact Info:**
• Admin Office: +91-12345-67890
• Email: admin@college.edu

---
*Complaint ID: {complaint.id} | Status: PENDING*"""
    
    def _lookup_qa(self, message: str) -> str:
        """Lookup Q&A from database"""
        # Simple keyword matching
        qa = ChatbotQA.query.filter(
            ChatbotQA.question.ilike(f'%{message}%')
        ).first()
        
        if qa:
            return qa.answer
        
        return None
    
    def _store_visitor_query(self, query_text: str, response_text: str, phone_number: str, query_type: str):
        """Store visitor query for tracking and analysis"""
        try:
            # Extract telegram user ID from phone number if it's a mapped user
            telegram_user_id = None
            if phone_number and phone_number.startswith('whatsapp:+'):
                # Try to find the telegram user mapping
                from app.models import TelegramUserMapping
                user_phone = phone_number.replace('whatsapp:+', '')
                mapping = TelegramUserMapping.query.filter_by(phone_number=user_phone).first()
                if mapping:
                    telegram_user_id = mapping.telegram_user_id
            
            # Create visitor query record
            visitor_query = VisitorQuery(
                query_type=query_type,
                query_text=query_text,
                response_text=response_text,
                phone_number=phone_number.replace('whatsapp:+', '') if phone_number else None,
                telegram_user_id=telegram_user_id
            )
            db.session.add(visitor_query)
            db.session.commit()
            
        except Exception as e:
            current_app.logger.error(f"Error storing visitor query: {str(e)}")
            db.session.rollback()
    
    def _store_unknown_query(self, message: str, phone_number: str, student_id: int = None):
        """Store unknown query as FAQ Record"""
        faq_record = FAQRecord(
            query=message,
            phone_number=phone_number,
            student_id=student_id
        )
        db.session.add(faq_record)
        db.session.commit()
        
        # Track analytics
        AnalyticsService.track_query()
