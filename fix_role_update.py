#!/usr/bin/env python3
"""
Script to fix faculty role update in edit function
"""

def fix_role_update():
    """Add role update line to edit faculty function"""
    
    with open('app/blueprints/admin.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the line with faculty.consultation_time and add role update after it
    for i, line in enumerate(lines):
        if 'faculty.consultation_time = consultation_time' in line:
            lines.insert(i + 1, '        faculty.role = role\n')
            break
    
    with open('app/blueprints/admin.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("Faculty role update fix applied successfully!")

if __name__ == "__main__":
    fix_role_update()
