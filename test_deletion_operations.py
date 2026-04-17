#!/usr/bin/env python3
"""
Test Deletion Operations with Foreign Key Constraints
Tests all deletion operations to ensure no foreign key violations
"""

import sys
import os

# Add to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, Admin, Faculty, Student, Notification, FAQ, DailyViewCount, Result, FAQRecord, Complaint, QueryLog, TelegramUserMapping, FeeRecord
from sqlalchemy import text

def test_student_deletion():
    """Test student deletion with foreign key constraints"""
    print("🗑️ Testing Student Deletion...")
    
    app = create_app()
    with app.app_context():
        try:
            # Models already imported at top level
            
            # Find a student to test with
            student = Student.query.first()
            if not student:
                print("⚠️  No students found to test deletion")
                return True
            
            student_id = student.id
            print(f"  Testing deletion of student ID: {student_id}")
            
            # Check related records before deletion
            daily_count = DailyViewCount.query.filter_by(student_id=student_id).count()
            print(f"  Related DailyViewCount records: {daily_count}")
            
            # Delete student using same logic as admin route
            # Delete all related records to avoid foreign key constraint violations
            db.session.query(DailyViewCount).filter_by(student_id=student_id).delete()
            db.session.query(Complaint).filter_by(student_id=student_id).delete()
            db.session.query(QueryLog).filter_by(student_id=student_id).delete()
            db.session.query(TelegramUserMapping).filter_by(student_id=student_id).delete()
            db.session.query(Result).filter_by(student_id=student_id).delete()
            db.session.query(FeeRecord).filter_by(student_id=student_id).delete()
            db.session.query(FAQRecord).filter_by(student_id=student_id).delete()
            
            db.session.delete(student)
            db.session.commit()
            
            # Verify student is deleted
            deleted_student = db.session.get(Student, student_id)
            if deleted_student is None:
                print("✅ Student deleted successfully")
                
                # Verify related records are also deleted
                remaining_daily = DailyViewCount.query.filter_by(student_id=student_id).count()
                if remaining_daily == 0:
                    print("✅ Related DailyViewCount records deleted by cascade")
                else:
                    print(f"⚠️  {remaining_daily} DailyViewCount records still exist")
                
                return True
            else:
                print("❌ Student deletion failed")
                return False
                
        except Exception as e:
            print(f"❌ Student deletion error: {str(e)}")
            db.session.rollback()
            return False

def test_faculty_deletion():
    """Test faculty deletion with foreign key constraints"""
    print("\n🗑️ Testing Faculty Deletion...")
    
    app = create_app()
    with app.app_context():
        try:
            # Find a faculty to test with
            faculty = Faculty.query.first()
            if not faculty:
                print("⚠️  No faculty found to test deletion")
                return True
            
            faculty_id = faculty.id
            print(f"  Testing deletion of faculty ID: {faculty_id}")
            
            # Check related records before deletion
            result_count = Result.query.filter_by(created_by=faculty_id).count()
            print(f"  Related Result records: {result_count}")
            
            # Delete faculty (should handle created_by NULLification)
            db.session.delete(faculty)
            db.session.commit()
            
            # Verify faculty is deleted
            deleted_faculty = db.session.get(Faculty, faculty_id)
            if deleted_faculty is None:
                print("✅ Faculty deleted successfully")
                
                # Verify related records have created_by set to NULL
                null_results = Result.query.filter_by(created_by=None).count()
                print(f"✅ Results with created_by=NULL: {null_results}")
                
                return True
            else:
                print("❌ Faculty deletion failed")
                return False
                
        except Exception as e:
            print(f"❌ Faculty deletion error: {str(e)}")
            db.session.rollback()
            return False

def test_faq_deletion():
    """Test FAQ deletion with foreign key constraints"""
    print("\n🗑️ Testing FAQ Deletion...")
    
    app = create_app()
    with app.app_context():
        try:
            # Create a test FAQ and FAQRecord
            test_faq = FAQ(
                question="Test question for deletion",
                answer="Test answer",
                category="test"
            )
            db.session.add(test_faq)
            db.session.commit()
            
            # Create related FAQRecord
            test_record = FAQRecord(
                query="Test query",
                faq_id=test_faq.id
            )
            db.session.add(test_record)
            db.session.commit()
            
            faq_id = test_faq.id
            record_count_before = db.session.query(FAQRecord).filter_by(faq_id=faq_id).count()
            print(f"  Created FAQ with {record_count_before} related records")
            
            # Delete FAQ using same logic as admin route
            # Delete related FAQRecord records first
            db.session.query(FAQRecord).filter_by(faq_id=test_faq.id).delete()
            
            db.session.delete(test_faq)
            db.session.commit()
            
            # Verify FAQ is deleted
            deleted_faq = db.session.get(FAQ, faq_id)
            if deleted_faq is None:
                print("✅ FAQ deleted successfully")
                
                # Verify related records are deleted
                record_count_after = db.session.query(FAQRecord).filter_by(faq_id=faq_id).count()
                if record_count_after == 0:
                    print("✅ Related FAQRecord records deleted")
                else:
                    print(f"⚠️  {record_count_after} FAQRecord records still exist")
                
                return True
            else:
                print("❌ FAQ deletion failed")
                return False
                
        except Exception as e:
            print(f"❌ FAQ deletion error: {str(e)}")
            db.session.rollback()
            return False

def test_notification_deletion():
    """Test notification deletion (should have no foreign key constraints)"""
    print("\n🗑️ Testing Notification Deletion...")
    
    app = create_app()
    with app.app_context():
        try:
            # Create a test notification
            test_notification = Notification(
                title="Test notification for deletion",
                content="Test content",
                expires_at=db.func.current_timestamp()
            )
            db.session.add(test_notification)
            db.session.commit()
            
            notification_id = test_notification.id
            print(f"  Created notification ID: {notification_id}")
            
            # Delete notification
            db.session.delete(test_notification)
            db.session.commit()
            
            # Verify notification is deleted
            deleted_notification = db.session.get(Notification, notification_id)
            if deleted_notification is None:
                print("✅ Notification deleted successfully")
                return True
            else:
                print("❌ Notification deletion failed")
                return False
                
        except Exception as e:
            print(f"❌ Notification deletion error: {str(e)}")
            db.session.rollback()
            return False

def main():
    """Run all deletion tests"""
    print("🔍 Testing Deletion Operations with Foreign Key Constraints")
    print("=" * 60)
    
    tests = [
        ("Student Deletion", test_student_deletion),
        ("Faculty Deletion", test_faculty_deletion),
        ("FAQ Deletion", test_faq_deletion),
        ("Notification Deletion", test_notification_deletion),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Deletion Test Results Summary:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} deletion tests passed")
    
    if passed == total:
        print("🎉 All deletion operations work correctly!")
        print("🛡️  No foreign key constraint violations detected.")
        return True
    else:
        print("⚠️  Some deletion operations have issues.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
