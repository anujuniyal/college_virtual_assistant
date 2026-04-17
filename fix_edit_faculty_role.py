#!/usr/bin/env python3
"""
Script to fix faculty role assignment in edit function
"""

def fix_edit_faculty_role():
    """Add role extraction and update to edit_faculty function"""
    
    with open('app/blueprints/admin.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the edit faculty function and add role extraction
    old_pattern = r'(consultation_time = request\.form\.get\(\'consultation_time\', \'\'\)\.strip\(\))'
    new_replacement = r'consultation_time = request.form.get(\'consultation_time\', \'\').strip()\n        role = request.form.get(\'role\', \'faculty\').strip()'
    
    content = content.replace(old_pattern, new_replacement)
    
    # Add role update to the faculty update section
    update_pattern = r'(faculty\.consultation_time = consultation_time)'
    update_replacement = r'faculty.consultation_time = consultation_time\n        faculty.role = role'
    
    content = content.replace(update_pattern, update_replacement)
    
    with open('app/blueprints/admin.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Edit faculty role assignment fix applied successfully!")

if __name__ == "__main__":
    fix_edit_faculty_role()
