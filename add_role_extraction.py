#!/usr/bin/env python3
"""
Script to add role extraction to edit faculty function
"""

def add_role_extraction():
    """Add role extraction line to edit faculty function"""
    
    with open('app/blueprints/admin.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add role extraction after consultation_time line
    old_line = "        consultation_time = request.form.get('consultation_time', '').strip()"
    new_line = "        consultation_time = request.form.get('consultation_time', '').strip()\n        role = request.form.get('role', 'faculty').strip()"
    
    content = content.replace(old_line, new_line)
    
    with open('app/blueprints/admin.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Role extraction added successfully!")

if __name__ == "__main__":
    add_role_extraction()
