#!/usr/bin/env python3
"""
Supabase Database Setup Script
Creates all necessary tables in Supabase PostgreSQL database
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Load environment variables
load_dotenv()

class SupabaseSetup:
    def __init__(self):
        self.supabase_url = os.environ.get('DATABASE_URL')
        
        if not self.supabase_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        # Convert postgres:// to postgresql:// for psycopg2
        if self.supabase_url.startswith('postgres://'):
            self.supabase_url = self.supabase_url.replace('postgres://', 'postgresql://', 1)
    
    def get_connection(self):
        """Get Supabase PostgreSQL connection"""
        return psycopg2.connect(self.supabase_url)
    
    def create_tables(self):
        """Create all necessary tables"""
        print("🏗️  Creating Supabase database tables...")
        
        tables_sql = """
        -- Admins table
        CREATE TABLE IF NOT EXISTS admins (
            id SERIAL PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) DEFAULT 'admin',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Students table
        CREATE TABLE IF NOT EXISTS students (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            roll_number VARCHAR(20) UNIQUE NOT NULL,
            email VARCHAR(120),
            phone VARCHAR(20),
            course VARCHAR(50),
            year VARCHAR(10),
            section VARCHAR(10),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Faculty table
        CREATE TABLE IF NOT EXISTS faculty (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            department VARCHAR(50),
            role VARCHAR(20) DEFAULT 'faculty',
            user_role VARCHAR(20) DEFAULT 'faculty',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Notifications table
        CREATE TABLE IF NOT EXISTS notifications (
            id SERIAL PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            message TEXT NOT NULL,
            notification_type VARCHAR(50) DEFAULT 'general',
            priority VARCHAR(20) DEFAULT 'medium',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        );
        
        -- Results table
        CREATE TABLE IF NOT EXISTS results (
            id SERIAL PRIMARY KEY,
            roll_number VARCHAR(20) NOT NULL,
            student_name VARCHAR(100) NOT NULL,
            exam_type VARCHAR(50),
            subject VARCHAR(50),
            marks INTEGER,
            total_marks INTEGER,
            percentage DECIMAL(5,2),
            grade VARCHAR(10),
            semester VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES admins(id)
        );
        
        -- Fee Records table
        CREATE TABLE IF NOT EXISTS fee_records (
            id SERIAL PRIMARY KEY,
            roll_number VARCHAR(20) NOT NULL,
            student_name VARCHAR(100) NOT NULL,
            fee_type VARCHAR(50),
            amount DECIMAL(10,2) NOT NULL,
            due_date DATE,
            payment_date DATE,
            status VARCHAR(20) DEFAULT 'pending',
            semester VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Complaints table
        CREATE TABLE IF NOT EXISTS complaints (
            id SERIAL PRIMARY KEY,
            roll_number VARCHAR(20),
            student_name VARCHAR(100),
            email VARCHAR(120),
            phone VARCHAR(20),
            category VARCHAR(50),
            subject VARCHAR(200),
            description TEXT,
            status VARCHAR(20) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Student Registrations table
        CREATE TABLE IF NOT EXISTS student_registrations (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            roll_number VARCHAR(20) UNIQUE NOT NULL,
            email VARCHAR(120),
            phone VARCHAR(20),
            course VARCHAR(50),
            year VARCHAR(10),
            section VARCHAR(10),
            status VARCHAR(20) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Telegram User Mappings table
        CREATE TABLE IF NOT EXISTS telegram_user_mappings (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT UNIQUE NOT NULL,
            roll_number VARCHAR(20),
            student_name VARCHAR(100),
            verified BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- OTP Verifications table
        CREATE TABLE IF NOT EXISTS otp_verifications (
            id SERIAL PRIMARY KEY,
            email VARCHAR(120) NOT NULL,
            otp VARCHAR(10) NOT NULL,
            purpose VARCHAR(20) DEFAULT 'login',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            is_used BOOLEAN DEFAULT FALSE
        );
        
        -- Predefined Info table
        CREATE TABLE IF NOT EXISTS predefined_info (
            id SERIAL PRIMARY KEY,
            section VARCHAR(50) NOT NULL,
            title VARCHAR(200) NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- FAQ Records table
        CREATE TABLE IF NOT EXISTS faq_records (
            id SERIAL PRIMARY KEY,
            query TEXT NOT NULL,
            response TEXT NOT NULL,
            category VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Chatbot QA table
        CREATE TABLE IF NOT EXISTS chatbot_qa (
            id SERIAL PRIMARY KEY,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            category VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Chatbot Unknown table
        CREATE TABLE IF NOT EXISTS chatbot_unknown (
            id SERIAL PRIMARY KEY,
            question TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(tables_sql)
            conn.commit()
            print("   ✅ All tables created successfully")
        except Exception as e:
            conn.rollback()
            print(f"   ❌ Error creating tables: {str(e)}")
            raise
        finally:
            conn.close()
    
    def create_indexes(self):
        """Create performance indexes"""
        print("📊 Creating performance indexes...")
        
        indexes_sql = """
        -- Performance indexes
        CREATE INDEX IF NOT EXISTS idx_admins_email ON admins(email);
        CREATE INDEX IF NOT EXISTS idx_admins_username ON admins(username);
        CREATE INDEX IF NOT EXISTS idx_admins_role ON admins(role);
        
        CREATE INDEX IF NOT EXISTS idx_students_roll_number ON students(roll_number);
        CREATE INDEX IF NOT EXISTS idx_students_email ON students(email);
        CREATE INDEX IF NOT EXISTS idx_students_course ON students(course);
        
        CREATE INDEX IF NOT EXISTS idx_faculty_email ON faculty(email);
        CREATE INDEX IF NOT EXISTS idx_faculty_role ON faculty(role);
        CREATE INDEX IF NOT EXISTS idx_faculty_department ON faculty(department);
        
        CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at);
        CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(notification_type);
        CREATE INDEX IF NOT EXISTS idx_notifications_priority ON notifications(priority);
        CREATE INDEX IF NOT EXISTS idx_notifications_active ON notifications(is_active);
        
        CREATE INDEX IF NOT EXISTS idx_results_roll_number ON results(roll_number);
        CREATE INDEX IF NOT EXISTS idx_results_semester ON results(semester);
        CREATE INDEX IF NOT EXISTS idx_results_exam_type ON results(exam_type);
        CREATE INDEX IF NOT EXISTS idx_results_created_at ON results(created_at);
        
        CREATE INDEX IF NOT EXISTS idx_fee_records_roll_number ON fee_records(roll_number);
        CREATE INDEX IF NOT EXISTS idx_fee_records_status ON fee_records(status);
        CREATE INDEX IF NOT EXISTS idx_fee_records_semester ON fee_records(semester);
        CREATE INDEX IF NOT EXISTS idx_fee_records_due_date ON fee_records(due_date);
        
        CREATE INDEX IF NOT EXISTS idx_complaints_created_at ON complaints(created_at);
        CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status);
        CREATE INDEX IF NOT EXISTS idx_complaints_category ON complaints(category);
        CREATE INDEX IF NOT EXISTS idx_complaints_roll_number ON complaints(roll_number);
        
        CREATE INDEX IF NOT EXISTS idx_student_registrations_created_at ON student_registrations(created_at);
        CREATE INDEX IF NOT EXISTS idx_student_registrations_status ON student_registrations(status);
        CREATE INDEX IF NOT EXISTS idx_student_registrations_roll_number ON student_registrations(roll_number);
        
        CREATE INDEX IF NOT EXISTS idx_telegram_user_mappings_telegram_id ON telegram_user_mappings(telegram_id);
        CREATE INDEX IF NOT EXISTS idx_telegram_user_mappings_roll_number ON telegram_user_mappings(roll_number);
        CREATE INDEX IF NOT EXISTS idx_telegram_user_mappings_verified ON telegram_user_mappings(verified);
        
        CREATE INDEX IF NOT EXISTS idx_otp_verifications_email ON otp_verifications(email);
        CREATE INDEX IF NOT EXISTS idx_otp_verifications_created_at ON otp_verifications(created_at);
        CREATE INDEX IF NOT EXISTS idx_otp_verifications_expires_at ON otp_verifications(expires_at);
        CREATE INDEX IF NOT EXISTS idx_otp_verifications_is_used ON otp_verifications(is_used);
        
        CREATE INDEX IF NOT EXISTS idx_predefined_info_section ON predefined_info(section);
        CREATE INDEX IF NOT EXISTS idx_predefined_info_title ON predefined_info(title);
        
        CREATE INDEX IF NOT EXISTS idx_faq_records_category ON faq_records(category);
        CREATE INDEX IF NOT EXISTS idx_faq_records_created_at ON faq_records(created_at);
        
        CREATE INDEX IF NOT EXISTS idx_chatbot_qa_category ON chatbot_qa(category);
        CREATE INDEX IF NOT EXISTS idx_chatbot_unknown_created_at ON chatbot_unknown(created_at);
        """
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(indexes_sql)
            conn.commit()
            print("   ✅ All indexes created successfully")
        except Exception as e:
            conn.rollback()
            print(f"   ❌ Error creating indexes: {str(e)}")
            raise
        finally:
            conn.close()
    
    def create_triggers(self):
        """Create triggers for updated_at timestamps"""
        print("⚡ Creating triggers...")
        
        triggers_sql = """
        -- Function to update updated_at timestamp
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        -- Triggers for tables with updated_at column
        CREATE TRIGGER update_admins_updated_at BEFORE UPDATE ON admins 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        
        CREATE TRIGGER update_students_updated_at BEFORE UPDATE ON students 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        
        CREATE TRIGGER update_faculty_updated_at BEFORE UPDATE ON faculty 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        
        CREATE TRIGGER update_fee_records_updated_at BEFORE UPDATE ON fee_records 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        
        CREATE TRIGGER update_complaints_updated_at BEFORE UPDATE ON complaints 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        
        CREATE TRIGGER update_student_registrations_updated_at BEFORE UPDATE ON student_registrations 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        
        CREATE TRIGGER update_telegram_user_mappings_updated_at BEFORE UPDATE ON telegram_user_mappings 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        
        CREATE TRIGGER update_predefined_info_updated_at BEFORE UPDATE ON predefined_info 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        
        CREATE TRIGGER update_faq_records_updated_at BEFORE UPDATE ON faq_records 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        
        CREATE TRIGGER update_chatbot_qa_updated_at BEFORE UPDATE ON chatbot_qa 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(triggers_sql)
            conn.commit()
            print("   ✅ All triggers created successfully")
        except Exception as e:
            conn.rollback()
            print(f"   ❌ Error creating triggers: {str(e)}")
            raise
        finally:
            conn.close()
    
    def setup_database(self):
        """Complete database setup"""
        print("🚀 Setting up Supabase database...")
        print("=" * 50)
        
        try:
            self.create_tables()
            self.create_indexes()
            self.create_triggers()
            
            print("=" * 50)
            print("✅ Supabase database setup completed successfully!")
            print("🎉 Your Supabase database is ready for migration!")
            
        except Exception as e:
            print(f"❌ Database setup failed: {str(e)}")
            sys.exit(1)
    
    def verify_setup(self):
        """Verify database setup"""
        print("🔍 Verifying database setup...")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        expected_tables = [
            'admins', 'students', 'faculty', 'notifications', 'results',
            'fee_records', 'complaints', 'student_registrations',
            'telegram_user_mappings', 'otp_verifications', 'predefined_info',
            'faq_records', 'chatbot_qa', 'chatbot_unknown'
        ]
        
        try:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """)
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            print(f"{'Table':<25} {'Status':<10}")
            print("-" * 35)
            
            all_exist = True
            for table in expected_tables:
                status = "✅ Exists" if table in existing_tables else "❌ Missing"
                if table not in existing_tables:
                    all_exist = False
                print(f"{table:<25} {status:<10}")
            
            print("-" * 35)
            if all_exist:
                print("✅ All expected tables exist!")
            else:
                print("⚠️  Some tables are missing. Please run setup again.")
            
        except Exception as e:
            print(f"❌ Verification failed: {str(e)}")
        finally:
            conn.close()

def main():
    """Main setup function"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        setup = SupabaseSetup()
        
        if command == "setup":
            setup.setup_database()
        elif command == "verify":
            setup.verify_setup()
        elif command == "full":
            setup.setup_database()
            setup.verify_setup()
        else:
            print("Usage: python setup_supabase.py [setup|verify|full]")
    else:
        print("Supabase Database Setup Tool")
        print("Usage: python setup_supabase.py [setup|verify|full]")
        print("")
        print("Commands:")
        print("  setup  - Create all tables, indexes, and triggers")
        print("  verify - Verify database setup")
        print("  full   - Setup and verify in one step")

if __name__ == "__main__":
    main()
