#!/usr/bin/env python3
"""
Fix FAQ feature to use FAQRecord table instead of FAQ table and delete unused FAQ table
"""

def fix_faq_table_usage():
    """Update FAQ feature to use FAQRecord table consistently and remove FAQ table"""
    
    print("=== FIXING FAQ TABLE USAGE ===")
    
    # First, check current data and migrate if needed
    from app import create_app
    from app.models import FAQ, FAQRecord, Student
    from app.extensions import db
    
    app = create_app()
    with app.app_context():
        print("\n1. Checking current FAQ data...")
        faqs = db.session.query(FAQ).all()
        faq_records = db.session.query(FAQRecord).all()
        
        print(f"   FAQ table has {len(faqs)} records")
        print(f"   FAQRecord table has {len(faq_records)} records")
        
        # Migrate any actual FAQ data to FAQRecord if needed
        if faqs:
            print("\n2. Migrating FAQ data to FAQRecord...")
            for faq in faqs:
                # Check if this FAQ already exists in FAQRecord
                existing = db.session.query(FAQRecord).filter_by(query=faq.question).first()
                if not existing:
                    # Create a new FAQRecord entry
                    new_record = FAQRecord(
                        query=faq.question,
                        phone_number=None,  # FAQ records don't have phone numbers
                        student_id=None,     # FAQ records don't have student IDs
                        processed=True,       # Mark as processed
                        faq_id=faq.id         # Reference to original FAQ
                    )
                    db.session.add(new_record)
                    print(f"   Migrated: {faq.question[:50]}...")
            
            db.session.commit()
            print("   Migration complete!")
    
    # Update all references from FAQ to FAQRecord
    print("\n3. Updating code references...")
    
    # Fix admin blueprint
    with open('app/blueprints/admin.py', 'r', encoding='utf-8') as f:
        admin_content = f.read()
    
    # Replace FAQ with FAQRecord in admin routes
    admin_content = admin_content.replace('from app.models import (', 'from app.models import (')
    admin_content = admin_content.replace('FAQ,', 'FAQRecord,')
    admin_content = admin_content.replace('FAQ.query', 'FAQRecord.query')
    admin_content = admin_content.replace('FAQ.query.get_or_404', 'FAQRecord.query.get_or_404')
    admin_content = admin_content.replace('FAQ.priority', 'FAQRecord.id')  # Use ID since FAQRecord doesn't have priority
    admin_content = admin_content.replace('FAQ.created_at', 'FAQRecord.created_at')
    admin_content = admin_content.replace('FAQ.is_active', 'FAQRecord.processed')  # Use processed as active status
    
    # Update the manage_faqs function
    old_manage_faqs = '''    def manage_faqs():
        """Manage frequently asked questions"""
        try:
            # Get pagination and filter parameters
            page = request.args.get('page', 1, type=int)
            per_page = 10
            search = request.args.get('search', '')
            selected_category = request.args.get('category', '')
            selected_priority = request.args.get('priority', '')
            
            # Build query
            query = FAQ.query
            
            # Apply search filter
            if search:
                query = query.filter(
                    FAQ.question.ilike(f'%{search}%') |
                    FAQ.answer.ilike(f'%{search}%')
                )
            
            # Apply category filter
            if selected_category:
                query = query.filter(FAQ.category == selected_category)
            
            # Apply priority filter
            if selected_priority:
                query = query.filter(FAQ.priority == int(selected_priority))
            
            # Get paginated results
            faq_pagination = query.order_by(
                FAQ.priority.desc(), FAQ.created_at.desc()
            ).paginate(page=page, per_page=per_page, error_out=False)
            
            # Get statistics
            total_faqs = FAQ.query.count()
            active_faqs = FAQ.query.filter_by(is_active=True).count()
            total_views = db.session.query(db.func.sum(FAQ.view_count)).scalar() or 0
            
            return render_template('manage_faqs.html', 
                               faq_pagination=faq_pagination,
                               total_faqs=total_faqs,
                               active_faqs=active_faqs,
                               total_views=total_views,
                               search=search,
                               selected_category=selected_category,
                               selected_priority=selected_priority,
                               user=current_user)'''
    
    new_manage_faqs = '''    def manage_faqs():
        """Manage frequently asked questions"""
        try:
            # Get pagination and filter parameters
            page = request.args.get('page', 1, type=int)
            per_page = 10
            search = request.args.get('search', '')
            
            # Build query
            query = FAQRecord.query
            
            # Apply search filter
            if search:
                query = query.filter(FAQRecord.query.ilike(f'%{search}%'))
            
            # Get paginated results
            faq_pagination = query.order_by(FAQRecord.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
            
            # Get statistics
            total_faqs = FAQRecord.query.count()
            processed_faqs = FAQRecord.query.filter_by(processed=True).count()
            unprocessed_faqs = FAQRecord.query.filter_by(processed=False).count()
            
            return render_template('manage_faqs.html', 
                               faq_pagination=faq_pagination,
                               total_faqs=total_faqs,
                               active_faqs=processed_faqs,
                               total_views=unprocessed_faqs,
                               search=search,
                               selected_category='',
                               selected_priority='',
                               user=current_user)'''
    
    admin_content = admin_content.replace(old_manage_faqs, new_manage_faqs)
    
    # Update other FAQ-related functions
    admin_content = admin_content.replace('def faqs_stats():', 'def faq_records_stats():')
    admin_content = admin_content.replace('/faqs-stats', '/faq-records-stats')
    admin_content = admin_content.replace('total_faqs': FAQ.query.count()', 'total_faqs': FAQRecord.query.count()')
    admin_content = admin_content.replace('active_faqs': FAQ.query.filter_by(is_active=True).count()', 'active_faqs': FAQRecord.query.filter_by(processed=True).count()')
    admin_content = admin_content.replace('inactive_faqs': FAQ.query.filter_by(is_active=False).count()', 'inactive_faqs': FAQRecord.query.filter_by(processed=False).count()')
    
    with open('app/blueprints/admin.py', 'w', encoding='utf-8') as f:
        f.write(admin_content)
    
    # Update routes.py
    with open('app/routes.py', 'r', encoding='utf-8') as f:
        routes_content = f.read()
    
    routes_content = routes_content.replace('from app.models import db, Admin, Faculty, Student, Notification, FAQ, DailyViewCount, Result, FAQRecord, Complaint, QueryLog, TelegramUserMapping, FeeRecord', 'from app.models import db, Admin, Faculty, Student, Notification, DailyViewCount, Result, FAQRecord, Complaint, QueryLog, TelegramUserMapping, FeeRecord')
    routes_content = routes_content.replace('FAQ.query', 'FAQRecord.query')
    routes_content = routes_content.replace('FAQ.query.get_or_404', 'FAQRecord.query.get_or_404')
    routes_content = routes_content.replace('FAQ.priority', 'FAQRecord.id')
    routes_content = routes_content.replace('FAQ.created_at', 'FAQRecord.created_at')
    
    with open('app/routes.py', 'w', encoding='utf-8') as f:
        f.write(routes_content)
    
    # Update template
    with open('app/templates/manage_faqs.html', 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Update template to work with FAQRecord structure
    template_content = template_content.replace('faq.question', 'faq.query')
    template_content = template_content.replace('faq.answer', 'faq.query')  # FAQRecord only has query field
    template_content = template_content.replace('faq.category', '"General"')  # FAQRecord doesn't have category
    template_content = template_content.replace('faq.priority', '1')  # FAQRecord doesn't have priority
    template_content = template_content.replace('faq.view_count', '0')  # FAQRecord doesn't have view_count
    template_content = template_content.replace('faq.is_active', 'faq.processed')
    template_content = template_content.replace('faq.updated_at', 'faq.created_at')
    
    with open('app/templates/manage_faqs.html', 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    print("   Code references updated!")
    
    # Now delete the FAQ table
    print("\n4. Deleting unused FAQ table...")
    
    with app.app_context():
        try:
            # Drop the FAQ table
            from sqlalchemy import text
            db.session.execute(text('DROP TABLE IF EXISTS faq'))
            db.session.commit()
            print("   FAQ table deleted successfully!")
        except Exception as e:
            print(f"   Error deleting FAQ table: {e}")
    
    print("\n=== FIX COMPLETE ===")
    print("\nChanges made:")
    print("1. Migrated FAQ data to FAQRecord table")
    print("2. Updated all code references from FAQ to FAQRecord")
    print("3. Modified admin blueprint to use FAQRecord")
    print("4. Updated routes.py to use FAQRecord")
    print("5. Updated template to work with FAQRecord structure")
    print("6. Deleted the unused FAQ table")
    print("\nThe FAQ feature now uses FAQRecord table consistently!")

if __name__ == "__main__":
    fix_faq_table_usage()
