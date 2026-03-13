"""
Faculty Setup Service
Creates faculty users with specified roles and passwords
"""

from flask import current_app
from werkzeug.security import generate_password_hash
from app.extensions import db
from app.models import Faculty


class FacultySetup:
    """Service for setting up faculty users with specific roles"""
    
    @staticmethod
    def create_specified_faculty():
        """Create the specified faculty users:
        - 1 admin: Sanjeev Raghav
        - 2 accounts users
        - Rest as faculty (total 5-7 users)
        """
        try:
            # Define faculty users to create
            faculty_users = [
                # Admin user
                {
                    'name': 'Sanjeev Raghav',
                    'email': 'sanjeev.raghav@edubot.com',
                    'department': 'Computer Science',
                    'role': 'admin',
                    'consultation_time': '10:00 AM - 12:00 PM',
                    'phone': '9876543210'
                },
                # Accounts users
                {
                    'name': 'Priya Sharma',
                    'email': 'priya.sharma@edubot.com',
                    'department': 'Accounts',
                    'role': 'accounts',
                    'consultation_time': '9:00 AM - 11:00 AM',
                    'phone': '9876543211'
                },
                {
                    'name': 'Amit Kumar',
                    'email': 'amit.kumar@edubot.com',
                    'department': 'Accounts',
                    'role': 'accounts',
                    'consultation_time': '2:00 PM - 4:00 PM',
                    'phone': '9876543212'
                },
                # Faculty users
                {
                    'name': 'Rajesh Singh',
                    'email': 'rajesh.singh@edubot.com',
                    'department': 'Computer Science',
                    'role': 'faculty',
                    'consultation_time': '11:00 AM - 1:00 PM',
                    'phone': '9876543213'
                },
                {
                    'name': 'Anita Verma',
                    'email': 'anita.verma@edubot.com',
                    'department': 'Information Technology',
                    'role': 'faculty',
                    'consultation_time': '3:00 PM - 5:00 PM',
                    'phone': '9876543214'
                },
                {
                    'name': 'Vikas Gupta',
                    'email': 'vikas.gupta@edubot.com',
                    'department': 'Electronics',
                    'role': 'faculty',
                    'consultation_time': '1:00 PM - 3:00 PM',
                    'phone': '9876543215'
                },
                {
                    'name': 'Sneha Patel',
                    'email': 'sneha.patel@edubot.com',
                    'department': 'Mechanical',
                    'role': 'faculty',
                    'consultation_time': '4:00 PM - 6:00 PM',
                    'phone': '9876543216'
                }
            ]
            
            created_users = []
            updated_users = []
            
            for user_data in faculty_users:
                # Generate password: facultyname + 123
                name_parts = user_data['name'].split()
                faculty_name = name_parts[0].lower()  # First name in lowercase
                password = f"{faculty_name}123"
                
                # Check if user already exists
                existing_faculty = Faculty.query.filter_by(email=user_data['email']).first()
                
                if existing_faculty:
                    # Update existing user
                    existing_faculty.name = user_data['name']
                    existing_faculty.department = user_data['department']
                    existing_faculty.role = user_data['role']
                    existing_faculty.consultation_time = user_data['consultation_time']
                    existing_faculty.phone = user_data['phone']
                    
                    # Update password
                    existing_faculty.set_password(password)
                    
                    updated_users.append({
                        'name': user_data['name'],
                        'email': user_data['email'],
                        'role': user_data['role'],
                        'password': password,
                        'action': 'updated'
                    })
                else:
                    # Create new user
                    new_faculty = Faculty(
                        name=user_data['name'],
                        email=user_data['email'],
                        department=user_data['department'],
                        role=user_data['role'],
                        consultation_time=user_data['consultation_time'],
                        phone=user_data['phone']
                    )
                    
                    # Set password
                    new_faculty.set_password(password)
                    
                    db.session.add(new_faculty)
                    
                    created_users.append({
                        'name': user_data['name'],
                        'email': user_data['email'],
                        'role': user_data['role'],
                        'password': password,
                        'action': 'created'
                    })
            
            # Commit all changes
            db.session.commit()
            
            # Log results
            current_app.logger.info(f"Created {len(created_users)} new faculty users")
            current_app.logger.info(f"Updated {len(updated_users)} existing faculty users")
            
            return {
                'success': True,
                'created': created_users,
                'updated': updated_users,
                'total': len(created_users) + len(updated_users)
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating faculty users: {str(e)}")
            return {
                'success': False,
                'message': f'Error creating faculty users: {str(e)}'
            }
    
    @staticmethod
    def get_faculty_by_role(role):
        """Get faculty users by role"""
        try:
            return Faculty.query.filter_by(role=role).all()
        except Exception as e:
            current_app.logger.error(f"Error getting faculty by role: {str(e)}")
            return []
    
    @staticmethod
    def list_all_faculty():
        """List all faculty users with their roles"""
        try:
            faculty_list = Faculty.query.order_by(Faculty.role, Faculty.name).all()
            
            result = []
            for faculty in faculty_list:
                result.append({
                    'id': faculty.id,
                    'name': faculty.name,
                    'email': faculty.email,
                    'department': faculty.department,
                    'role': faculty.role,
                    'consultation_time': faculty.consultation_time,
                    'phone': faculty.phone,
                    'created_at': faculty.created_at
                })
            
            return result
            
        except Exception as e:
            current_app.logger.error(f"Error listing faculty: {str(e)}")
            return []
    
    @staticmethod
    def authenticate_faculty(email, password):
        """Authenticate faculty user"""
        try:
            faculty = Faculty.query.filter_by(email=email).first()
            
            if not faculty:
                return {'success': False, 'message': 'Faculty not found'}
            
            if not faculty.check_password(password):
                return {'success': False, 'message': 'Invalid password'}
            
            return {
                'success': True,
                'faculty': faculty,
                'message': f'Authenticated as {faculty.name} ({faculty.role})'
            }
            
        except Exception as e:
            current_app.logger.error(f"Error authenticating faculty: {str(e)}")
            return {'success': False, 'message': 'Authentication failed'}
    
    @staticmethod
    def update_faculty_role(faculty_id, new_role):
        """Update faculty user role"""
        try:
            faculty = Faculty.query.get(faculty_id)
            if not faculty:
                return {'success': False, 'message': 'Faculty not found'}
            
            valid_roles = ['admin', 'faculty', 'accounts']
            if new_role not in valid_roles:
                return {'success': False, 'message': f'Invalid role. Must be one of: {", ".join(valid_roles)}'}
            
            faculty.role = new_role
            db.session.commit()
            
            return {
                'success': True,
                'message': f'Updated {faculty.name} role to {new_role}'
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating faculty role: {str(e)}")
            return {'success': False, 'message': 'Error updating role'}
    
    @staticmethod
    def reset_faculty_password(faculty_id):
        """Reset faculty password to default (name + 123)"""
        try:
            faculty = Faculty.query.get(faculty_id)
            if not faculty:
                return {'success': False, 'message': 'Faculty not found'}
            
            # Generate default password
            name_parts = faculty.name.split()
            faculty_name = name_parts[0].lower()
            new_password = f"{faculty_name}123"
            
            faculty.set_password(new_password)
            db.session.commit()
            
            return {
                'success': True,
                'message': f'Password reset for {faculty.name}',
                'password': new_password
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error resetting faculty password: {str(e)}")
            return {'success': False, 'message': 'Error resetting password'}
