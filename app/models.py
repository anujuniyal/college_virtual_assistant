"""
Database Models
"""
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db
from app.config import Config


class Admin(UserMixin, db.Model):
    """Admin/Faculty/Accounts user model"""
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'faculty', 'accounts'
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<Admin {self.username}>'


class Student(db.Model, UserMixin):
    """Student model"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    roll_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False, index=True)
    email = db.Column(db.String(120))
    department = db.Column(db.String(50))
    semester = db.Column(db.Integer)
    telegram_user_id = db.Column(db.String(32), nullable=True, index=True)  # Telegram authentication
    telegram_verified = db.Column(db.Boolean, default=False, nullable=False)  # Verification status
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    results = db.relationship('Result', backref='student', lazy=True, cascade='all, delete-orphan')
    fee_records = db.relationship('FeeRecord', backref='student', lazy=True, cascade='all, delete-orphan')
    complaints = db.relationship('Complaint', backref='student', lazy=True)
    query_logs = db.relationship('QueryLog', backref='student', lazy=True)
    telegram_mappings = db.relationship('TelegramUserMapping', backref='student_record', lazy=True)
    
    def link_telegram_account(self, telegram_user_id):
        """Link Telegram account to student with proper transaction handling"""
        from app.extensions import db
        from sqlalchemy.exc import IntegrityError
        
        try:
            # Start transaction
            # Update student record first
            self.telegram_user_id = telegram_user_id
            self.telegram_verified = True
            
            # Also update the TelegramUserMapping table
            existing_mapping = TelegramUserMapping.query.filter_by(
                phone_number=self.phone,
                telegram_user_id=telegram_user_id
            ).first()
            
            if not existing_mapping:
                mapping = TelegramUserMapping(
                    telegram_user_id=telegram_user_id,
                    student_id=self.id,
                    phone_number=self.phone,
                    verified=True
                )
                db.session.add(mapping)
            else:
                # Update existing mapping
                existing_mapping.student_id = self.id
                existing_mapping.verified = True
            
            # Commit transaction
            db.session.commit()
            return True, "Telegram account linked successfully"
            
        except IntegrityError as e:
            db.session.rollback()
            return False, f"Database integrity error: {str(e)}"
        except Exception as e:
            db.session.rollback()
            return False, f"Error linking Telegram account: {str(e)}"
    
    def unlink_telegram_account(self):
        """Unlink Telegram account from student with proper transaction handling"""
        from app.extensions import db
        from sqlalchemy.exc import IntegrityError
        
        try:
            # Start transaction
            self.telegram_user_id = None
            self.telegram_verified = False
            
            # Remove from TelegramUserMapping table
            TelegramUserMapping.query.filter_by(student_id=self.id).delete()
            
            # Commit transaction
            db.session.commit()
            return True, "Telegram account unlinked successfully"
            
        except IntegrityError as e:
            db.session.rollback()
            return False, f"Database integrity error: {str(e)}"
        except Exception as e:
            db.session.rollback()
            return False, f"Error unlinking Telegram account: {str(e)}"
    
    def is_telegram_verified(self):
        """Check if student has verified Telegram account"""
        return self.telegram_verified and self.telegram_user_id is not None
    
    def get_telegram_info(self):
        """Get Telegram verification info"""
        if self.is_telegram_verified():
            return {
                'verified': True,
                'telegram_user_id': self.telegram_user_id,
                'phone': self.phone
            }
        else:
            return {
                'verified': False,
                'telegram_user_id': None,
                'phone': self.phone,
                'message': 'Student needs to verify via Telegram bot'
            }
    
    @property
    def role(self):
        """Return user role"""
        return 'student'
    
    def __repr__(self):
        return f'<Student {self.roll_number}>'


class Notification(db.Model):
    """Digital Notice Board"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    file_url = db.Column(db.String(500))
    link_url = db.Column(db.String(500))
    notification_type = db.Column(db.String(50), default='general', nullable=False)
    priority = db.Column(db.String(20), default='medium', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('admins.id'))
    
    def is_expired(self):
        """Check if notification is expired"""
        return datetime.utcnow() > self.expires_at
    
    def __repr__(self):
        return f'<Notification {self.title}>'


class Result(db.Model):
    """Student Results"""
    __tablename__ = 'results'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    marks = db.Column(db.Float, nullable=False)
    grade = db.Column(db.String(5))
    declared_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Auto-delete/reset window: default one week after declaration unless overridden.
    semester_end_date = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.utcnow() + timedelta(days=Config.RESULT_VISIBILITY_DAYS),
    )
    # "Issued by" info (faculty/admin who uploaded the result record)
    created_by = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)
    
    def is_visible(self):
        """Check if result is still visible (within visibility period)"""
        return (datetime.utcnow() - self.declared_at) <= timedelta(days=Config.RESULT_VISIBILITY_DAYS)
    
    def should_be_deleted(self):
        """Check if result should be deleted (after semester end)"""
        return datetime.utcnow() > self.semester_end_date
    
    def __repr__(self):
        return f'<Result {self.student_id} - {self.subject}>'


class FeeRecord(db.Model):
    """Fee Records"""
    __tablename__ = 'fee_records'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    paid_amount = db.Column(db.Float, default=0.0)
    balance_amount = db.Column(db.Float, nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def balance(self):
        """Calculate balance"""
        return self.total_amount - self.paid_amount
    
    def update_balance(self):
        """Update balance_amount field to match calculated balance"""
        self.balance_amount = self.balance
    
    def __repr__(self):
        return f'<FeeRecord {self.student_id} - Sem {self.semester}>'


class Faculty(db.Model, UserMixin):
    """Faculty Information"""
    __tablename__ = 'faculty'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    department = db.Column(db.String(50), nullable=False)
    consultation_time = db.Column(db.String(100))
    phone = db.Column(db.String(15))
    role = db.Column(db.String(20), nullable=False, default='faculty')  # admin, accounts, faculty
    password_hash = db.Column(db.String(255))  # Add password field
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    @property
    def user_role(self):
        """Return user role from role field"""
        return self.role
    
    @property
    def username(self):
        """Return username (email for compatibility)"""
        return self.email
    
    def __repr__(self):
        return f'<Faculty {self.name} ({self.role})>'


class Complaint(db.Model):
    """Anti-Ragging Complaints"""
    __tablename__ = 'complaints'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # 'ragging', 'harassment', 'other'
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'investigating', 'resolved'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Complaint {self.id} - {self.category}>'


class ChatbotQA(db.Model):
    """Pre-fed Chatbot Q&A"""
    __tablename__ = 'chatbot_qa'
    
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False, index=True)
    answer = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))  # 'admission', 'course', 'fee', 'facilities'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ChatbotQA {self.id}>'


class PredefinedInfo(db.Model):
    """Predefined College Information - Editable by Admin"""
    __tablename__ = 'predefined_info'
    
    id = db.Column(db.Integer, primary_key=True)
    section = db.Column(db.String(50), nullable=False, index=True)  # 'admission', 'fees', 'facilities', etc.
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))  # sub-category within section
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)
    
    def __repr__(self):
        return f'<PredefinedInfo {self.section}: {self.title}>'

class FAQ(db.Model):
    """Frequently Asked Questions - High Frequency Queries"""
    __tablename__ = 'faq'
    
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False, index=True)
    answer = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))  # 'admission', 'fees', 'facilities', etc.
    priority = db.Column(db.Integer, default=1)  # 1=low, 2=medium, 3=high
    view_count = db.Column(db.Integer, default=0)  # Track popularity
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)
    
    def __repr__(self):
        return f'<FAQ {self.id}: {self.question[:50]}...>'

class FAQRecord(db.Model):
    """FAQ Records - Questions from visitors/students to be processed"""
    __tablename__ = 'faq_records'
    
    id = db.Column(db.Integer, primary_key=True)
    query = db.Column(db.Text, nullable=False)
    phone_number = db.Column(db.String(15))
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed = db.Column(db.Boolean, default=False)  # renamed from exported
    faq_id = db.Column(db.Integer, db.ForeignKey('faq.id'), nullable=True)  # link to created FAQ
    
    def __repr__(self):
        return f'<FAQRecord {self.id}: {self.query[:50]}...>'


class QueryLog(db.Model):
    """Query Logs for Rate Limiting"""
    __tablename__ = 'query_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)
    phone_number = db.Column(db.String(15), nullable=True)
    query_type = db.Column(db.String(20), nullable=False)  # 'result', 'fee'
    query_date = db.Column(db.Date, default=datetime.utcnow().date, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_student_query', 'student_id', 'query_type', 'query_date'),
        db.Index('idx_phone_query', 'phone_number', 'query_type', 'query_date'),
    )
    
    def __repr__(self):
        return f'<QueryLog {self.query_type} - {self.query_date}>'


class OTP(db.Model):
    """OTP for Faculty Verification"""
    __tablename__ = 'otps'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    otp_code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    
    def is_expired(self):
        """Check if OTP is expired"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """Check if OTP is valid and not used"""
        return not self.used and not self.is_expired()
    
    def __repr__(self):
        return f'<OTP {self.email}>'


class Session(db.Model):
    """WhatsApp Session Management"""
    __tablename__ = 'sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(15), unique=True, nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)
    verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Session {self.phone_number}>'


class DailyViewCount(db.Model):
    """Daily view count tracking for student services"""
    __tablename__ = 'daily_view_counts'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    service_type = db.Column(db.String(20), nullable=False)  # 'result' or 'fee'
    view_date = db.Column(db.Date, nullable=False)
    view_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint for one record per student per service per day
    __table_args__ = (
        db.UniqueConstraint('student_id', 'service_type', 'view_date', name='unique_daily_view'),
    )
    
    def can_view(self, max_daily_views=5):
        """Check if student can view this service today"""
        return self.view_count < max_daily_views
    
    def get_remaining_views(self, max_daily_views=5):
        """Get remaining views for today"""
        return max(0, max_daily_views - self.view_count)
    
    def increment_view(self):
        """Increment view count for today"""
        self.view_count += 1
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def __repr__(self):
        return f'<DailyViewCount {self.student_id} {self.service_type} {self.view_date}>'


class StudentRegistration(db.Model):
    """Student Registration Records - for approval process"""
    __tablename__ = 'student_registrations'
    
    id = db.Column(db.Integer, primary_key=True)
    roll_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False, index=True)
    email = db.Column(db.String(120))
    department = db.Column(db.String(50))
    semester = db.Column(db.Integer)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'
    approved_at = db.Column(db.DateTime)
    approved_by = db.Column(db.Integer, db.ForeignKey('admins.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def approve(self, admin_id):
        """Approve registration and transfer to student table"""
        try:
            # Create student record
            student = Student(
                roll_number=self.roll_number,
                name=self.name,
                phone=self.phone,
                email=self.email,
                department=self.department,
                semester=self.semester
            )
            
            # Update registration status
            self.status = 'approved'
            self.approved_at = datetime.utcnow()
            self.approved_by = admin_id
            
            db.session.add(student)
            db.session.commit()
            
            return True, student
        except Exception as e:
            db.session.rollback()
            return False, str(e)
    
    def reject(self, admin_id):
        """Reject registration"""
        self.status = 'rejected'
        self.approved_at = datetime.utcnow()
        self.approved_by = admin_id
        db.session.commit()
    
    def __repr__(self):
        return f'<StudentRegistration {self.roll_number} - {self.status}>'


class TelegramUserMapping(db.Model):
    """Telegram user ID -> phone number (and optionally verified student)."""
    __tablename__ = 'telegram_user_mappings'

    id = db.Column(db.Integer, primary_key=True)
    telegram_user_id = db.Column(db.String(32), unique=True, nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True, index=True)
    phone_number = db.Column(db.String(15), nullable=False, index=True)
    verified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    student = db.relationship('Student', lazy=True)

    def __repr__(self):
        return f'<TelegramUserMapping {self.telegram_user_id} -> {self.phone_number}>'


class VisitorQuery(db.Model):
    """Visitor mode queries for tracking and analysis"""
    __tablename__ = 'visitor_queries'
    
    id = db.Column(db.Integer, primary_key=True)
    query_type = db.Column(db.String(50), nullable=False)  # 'admission', 'course', 'fee', 'facilities', 'faculty', 'other'
    query_text = db.Column(db.Text, nullable=False)
    response_text = db.Column(db.Text, nullable=False)
    phone_number = db.Column(db.String(15), nullable=True)  # Optional for anonymous visitors
    telegram_user_id = db.Column(db.String(32), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<VisitorQuery {self.query_type} - {self.id}>'
