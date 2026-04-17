#!/usr/bin/env python3
"""
Script to fix student deletion to handle foreign key constraints properly
"""

def fix_student_deletion():
    """Fix student deletion to handle all foreign key constraints"""
    
    with open('app/blueprints/admin.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace the simple student deletion with proper foreign key handling
    old_deletion = '''    try:
        student = Student.query.get_or_404(student_id)
        db.session.delete(student)
        db.session.commit()
        
        flash('Student deleted successfully.', 'success')
        return redirect(url_for('admin.manage_students'))
        
    except Exception as e:
        current_app.logger.error(f"Error deleting student: {str(e)}")
        flash('Error deleting student. Please try again.', 'error')
        return redirect(url_for('admin.manage_students'))'''
    
    new_deletion = '''    try:
        student = Student.query.get_or_404(student_id)
        
        # Handle all foreign key constraints manually before deletion
        from app.models import DailyViewCount, Complaint, QueryLog, TelegramUserMapping, Result, FeeRecord, FAQRecord, Session
        
        # Delete all related records to avoid foreign key constraint violations
        db.session.query(Session).filter_by(student_id=student_id).delete()
        db.session.query(DailyViewCount).filter_by(student_id=student_id).delete()
        db.session.query(Complaint).filter_by(student_id=student_id).delete()
        db.session.query(QueryLog).filter_by(student_id=student_id).delete()
        db.session.query(TelegramUserMapping).filter_by(student_id=student_id).delete()
        db.session.query(Result).filter_by(student_id=student_id).delete()
        db.session.query(FeeRecord).filter_by(student_id=student_id).delete()
        db.session.query(FAQRecord).filter_by(student_id=student_id).delete()
        
        db.session.delete(student)
        db.session.commit()
        
        flash('Student deleted successfully.', 'success')
        return redirect(url_for('admin.manage_students'))
        
    except Exception as e:
        current_app.logger.error(f"Error deleting student: {str(e)}")
        flash('Error deleting student. Please try again.', 'error')
        return redirect(url_for('admin.manage_students'))'''
    
    content = content.replace(old_deletion, new_deletion)
    
    with open('app/blueprints/admin.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Student deletion fix applied successfully!")

if __name__ == "__main__":
    fix_student_deletion()
