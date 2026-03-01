"""
Database Upload Service for Excel/CSV file processing
"""

import pandas as pd
import os
from datetime import datetime, date
from flask import current_app
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Student, Faculty, FeeRecord, Result

class DatabaseUploadService:
    """Service for handling database uploads from Excel/CSV files"""
    
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
    
    @staticmethod
    def allowed_file(filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in DatabaseUploadService.ALLOWED_EXTENSIONS
    
    @staticmethod
    def read_file(file_path):
        """Read Excel or CSV file and return DataFrame"""
        try:
            if file_path.endswith('.csv'):
                return pd.read_csv(file_path)
            else:  # Excel file
                return pd.read_excel(file_path)
        except Exception as e:
            raise ValueError(f"Error reading file: {str(e)}")
    
    @staticmethod
    def clean_column_names(df):
        """Clean and standardize column names"""
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        return df
    
    @staticmethod
    def get_default_values(model_name):
        """Get default values for missing fields"""
        defaults = {
            'student': {
                'address': 'Not Provided',
                'date_of_birth': None,
                'gender': 'Not Specified',
                'blood_group': 'Not Specified'
            },
            'faculty': {
                'phone': 'Not Provided',
                'consultation_time': 'Not Specified',
                'designation': 'Faculty',
                'qualification': 'Not Specified'
            },
            'fee': {
                'payment_date': datetime.utcnow().date(),
                'payment_method': 'Not Specified',
                'remarks': 'Not Provided'
            },
            'result': {
                'exam_date': datetime.utcnow().date(),
                'remarks': 'Not Provided'
            }
        }
        return defaults.get(model_name, {})
    
    @staticmethod
    def upload_students(file_path, mode='append'):
        """Upload students data from file"""
        try:
            # Read and clean data
            df = DatabaseUploadService.read_file(file_path)
            df = DatabaseUploadService.clean_column_names(df)
            
            # Get defaults
            defaults = DatabaseUploadService.get_default_values('student')
            
            # Required fields
            required_fields = ['roll_number', 'name', 'phone', 'email', 'department', 'semester']
            
            # Check required fields
            missing_fields = [field for field in required_fields if field not in df.columns]
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            
            # Replace mode: delete existing data
            if mode == 'replace':
                Student.query.delete()
                db.session.commit()
            
            uploaded_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Check if student exists (for append mode)
                    if mode == 'append':
                        existing = Student.query.filter_by(roll_number=str(row['roll_number'])).first()
                        if existing:
                            continue  # Skip existing records in append mode
                    
                    # Create student record
                    student = Student(
                        roll_number=str(row['roll_number']),
                        name=str(row['name']),
                        phone=str(row['phone']),
                        email=str(row['email']),
                        department=str(row['department']),
                        semester=int(row['semester']) if pd.notna(row['semester']) else 1,
                        address=str(row.get('address', defaults['address'])),
                        date_of_birth=pd.to_datetime(row['date_of_birth']).date() if pd.notna(row.get('date_of_birth')) else defaults['date_of_birth'],
                        gender=str(row.get('gender', defaults['gender'])),
                        blood_group=str(row.get('blood_group', defaults['blood_group']))
                    )
                    
                    db.session.add(student)
                    uploaded_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
                    continue
            
            db.session.commit()
            
            return {
                'success': True,
                'uploaded': uploaded_count,
                'errors': errors,
                'message': f'Successfully uploaded {uploaded_count} student records.'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'uploaded': 0,
                'errors': [str(e)],
                'message': f'Error uploading students: {str(e)}'
            }
    
    @staticmethod
    def upload_faculty(file_path, mode='append'):
        """Upload faculty data from file"""
        try:
            # Read and clean data
            df = DatabaseUploadService.read_file(file_path)
            df = DatabaseUploadService.clean_column_names(df)
            
            # Get defaults
            defaults = DatabaseUploadService.get_default_values('faculty')
            
            # Required fields
            required_fields = ['name', 'email', 'department']
            
            # Check required fields
            missing_fields = [field for field in required_fields if field not in df.columns]
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            
            # Replace mode: delete existing data
            if mode == 'replace':
                Faculty.query.delete()
                db.session.commit()
            
            uploaded_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Check if faculty exists (for append mode)
                    if mode == 'append':
                        existing = Faculty.query.filter_by(email=str(row['email'])).first()
                        if existing:
                            continue  # Skip existing records in append mode
                    
                    # Create faculty record
                    faculty = Faculty(
                        name=str(row['name']),
                        email=str(row['email']),
                        department=str(row['department']),
                        phone=str(row.get('phone', defaults['phone'])),
                        consultation_time=str(row.get('consultation_time', defaults['consultation_time'])),
                        designation=str(row.get('designation', defaults['designation'])),
                        qualification=str(row.get('qualification', defaults['qualification']))
                    )
                    
                    db.session.add(faculty)
                    uploaded_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
                    continue
            
            db.session.commit()
            
            return {
                'success': True,
                'uploaded': uploaded_count,
                'errors': errors,
                'message': f'Successfully uploaded {uploaded_count} faculty records.'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'uploaded': 0,
                'errors': [str(e)],
                'message': f'Error uploading faculty: {str(e)}'
            }
    
    @staticmethod
    def upload_fees(file_path, mode='append'):
        """Upload fee data from file"""
        try:
            # Read and clean data
            df = DatabaseUploadService.read_file(file_path)
            df = DatabaseUploadService.clean_column_names(df)
            
            # Get defaults
            defaults = DatabaseUploadService.get_default_values('fee')
            
            # Required fields
            required_fields = ['roll_number', 'semester', 'total_amount', 'paid_amount']
            
            # Check required fields
            missing_fields = [field for field in required_fields if field not in df.columns]
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            
            # Replace mode: delete existing data
            if mode == 'replace':
                FeeRecord.query.delete()
                db.session.commit()
            
            uploaded_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Find student by roll number
                    student = Student.query.filter_by(roll_number=str(row['roll_number'])).first()
                    if not student:
                        errors.append(f"Row {index + 1}: Student with roll number {row['roll_number']} not found")
                        continue
                    
                    # Calculate balance
                    total_amount = float(row['total_amount'])
                    paid_amount = float(row['paid_amount'])
                    balance_amount = total_amount - paid_amount
                    
                    # Create fee record
                    fee_record = FeeRecord(
                        student_id=student.id,
                        semester=int(row['semester']) if pd.notna(row['semester']) else 1,
                        total_amount=total_amount,
                        paid_amount=paid_amount,
                        balance_amount=balance_amount,
                        payment_date=pd.to_datetime(row.get('payment_date', defaults['payment_date'])).date(),
                        payment_method=str(row.get('payment_method', defaults['payment_method'])),
                        remarks=str(row.get('remarks', defaults['remarks']))
                    )
                    
                    db.session.add(fee_record)
                    uploaded_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
                    continue
            
            db.session.commit()
            
            return {
                'success': True,
                'uploaded': uploaded_count,
                'errors': errors,
                'message': f'Successfully uploaded {uploaded_count} fee records.'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'uploaded': 0,
                'errors': [str(e)],
                'message': f'Error uploading fees: {str(e)}'
            }
    
    @staticmethod
    def upload_results(file_path, mode='append'):
        """Upload results data from file"""
        try:
            # Read and clean data
            df = DatabaseUploadService.read_file(file_path)
            df = DatabaseUploadService.clean_column_names(df)
            
            # Get defaults
            defaults = DatabaseUploadService.get_default_values('result')
            
            # Required fields
            required_fields = ['roll_number', 'semester', 'subject', 'marks', 'grade']
            
            # Check required fields
            missing_fields = [field for field in required_fields if field not in df.columns]
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            
            # Replace mode: delete existing data
            if mode == 'replace':
                Result.query.delete()
                db.session.commit()
            
            uploaded_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Find student by roll number
                    student = Student.query.filter_by(roll_number=str(row['roll_number'])).first()
                    if not student:
                        errors.append(f"Row {index + 1}: Student with roll number {row['roll_number']} not found")
                        continue
                    
                    # Create result record
                    result = Result(
                        student_id=student.id,
                        semester=int(row['semester']) if pd.notna(row['semester']) else 1,
                        subject=str(row['subject']),
                        marks=float(row['marks']),
                        grade=str(row['grade']),
                        exam_date=pd.to_datetime(row.get('exam_date', defaults['exam_date'])).date(),
                        remarks=str(row.get('remarks', defaults['remarks'])),
                        declared_at=datetime.utcnow()
                    )
                    
                    db.session.add(result)
                    uploaded_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
                    continue
            
            db.session.commit()
            
            return {
                'success': True,
                'uploaded': uploaded_count,
                'errors': errors,
                'message': f'Successfully uploaded {uploaded_count} result records.'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'uploaded': 0,
                'errors': [str(e)],
                'message': f'Error uploading results: {str(e)}'
            }
