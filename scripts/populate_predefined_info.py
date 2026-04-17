#!/usr/bin/env python3
"""
Populate PredefinedInfo table with current static values from bot service
"""
import sys
import os
from datetime import datetime

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import PredefinedInfo, Admin

def populate_predefined_info():
    """Populate predefined info with current static bot values"""
    app = create_app()
    
    with app.app_context():
        # Get admin user (first admin available)
        admin = Admin.query.first()
        admin_id = admin.id if admin else None
        
        # Static values from bot service
        predefined_data = [
            {
                'section': 'admission',
                'title': 'Admission Process',
                'category': 'process',
                'content': """📚 **ADMISSION PROCESS**

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

Issued by: Admission Department""",
                'is_active': True
            },
            {
                'section': 'courses',
                'title': 'Courses & Fee Structure',
                'category': 'programs',
                'content': """📖 **COURSES & FEE STRUCTURE**

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

Issued by: Academic Department""",
                'is_active': True
            },
            {
                'section': 'fees',
                'title': 'General Fee Structure',
                'category': 'overview',
                'content': """💰 FEE STRUCTURE (General)

B.Tech: ₹1,50,000/year
BBA: ₹80,000/year
BCA: ₹70,000/year
M.Tech: ₹1,00,000/year
MBA: ₹1,20,000/year

*Includes tuition, library, lab fees
*Hostel fees separate

For detailed breakdown, verify your roll number and check 'fee' command.

Issued by: Accounts Section""",
                'is_active': True
            },
            {
                'section': 'facilities',
                'title': 'College Facilities',
                'category': 'infrastructure',
                'content': """🏫 COLLEGE FACILITIES

• Library with 50,000+ books
• Computer Labs (24/7)
• Sports Complex
• Hostel (Boys & Girls)
• Cafeteria
• Medical Center
• Wi-Fi Campus
• Auditorium

For more details, visit: www.college.edu/facilities

Issued by: College Admin""",
                'is_active': True
            },
            {
                'section': 'contact',
                'title': 'College Contact Information',
                'category': 'general',
                'content': """📞 **COLLEGE CONTACT INFORMATION**

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

Issued by: College Administration""",
                'is_active': True
            }
        ]
        
        # Clear existing predefined info
        print("Clearing existing predefined info...")
        PredefinedInfo.query.delete()
        db.session.commit()
        
        # Add new predefined info
        print("Adding predefined info...")
        for data in predefined_data:
            info = PredefinedInfo(
                section=data['section'],
                title=data['title'],
                content=data['content'],
                category=data.get('category'),
                is_active=data['is_active'],
                updated_by=admin_id
            )
            db.session.add(info)
            print(f"Added: {data['section']} - {data['title']}")
        
        db.session.commit()
        print(f"\n✅ Successfully populated {len(predefined_data)} predefined info entries!")

if __name__ == '__main__':
    populate_predefined_info()
