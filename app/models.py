"""
Database Models
"""
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db


class Admin(UserMixin, db.Model):
    """Admin/Faculty/Accounts user model"""
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'faculty', 'accounts'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<Admin {self.username}>'


class Student(db.Model):
    """Student model"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    roll_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False, index=True)
    email = db.Column(db.String(120))
    department = db.Column(db.String(50))
    semester = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    results = db.relationship('Result', backref='student', lazy=True, cascade='all, delete-orphan')
    fee_records = db.relationship('FeeRecord', backref='student', lazy=True, cascade='all, delete-orphan')
    complaints = db.relationship('Complaint', backref='student', lazy=True)
    query_logs = db.relationship('QueryLog', backref='student', lazy=True)
    
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
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
    semester_end_date = db.Column(db.DateTime, nullable=False)
    
    def is_visible(self):
        """Check if result is still visible (within visibility period)"""
        days_since_declaration = (datetime.utcnow() - self.declared_at).days
        return days_since_declaration <= Config.RESULT_VISIBILITY_DAYS
    
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
    
    def __repr__(self):
        return f'<FeeRecord {self.student_id} - Sem {self.semester}>'


class Faculty(db.Model):
    """Faculty Information"""
    __tablename__ = 'faculty'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    department = db.Column(db.String(50), nullable=False)
    consultation_time = db.Column(db.String(100))
    phone = db.Column(db.String(15))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Faculty {self.name}>'


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


class ChatbotUnknown(db.Model):
    """Unknown Chatbot Queries"""
    __tablename__ = 'chatbot_unknown'
    
    id = db.Column(db.Integer, primary_key=True)
    query = db.Column(db.Text, nullable=False)
    phone_number = db.Column(db.String(15))
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    exported = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<ChatbotUnknown {self.id}>'


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
