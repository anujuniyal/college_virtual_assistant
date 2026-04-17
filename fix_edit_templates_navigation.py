#!/usr/bin/env python3
"""
Fix edit-student and edit-faculty templates to use consistent sidebar navigation
"""

def fix_edit_templates_navigation():
    """Add consistent sidebar navigation to edit-student and edit-faculty templates"""
    
    print("=== FIXING EDIT TEMPLATES SIDEBAR NAVIGATION ===")
    
    # Define the standard sidebar navigation structure
    standard_sidebar = '''{% block sidebar_nav %}
<!-- Admin Navigation -->
<div class="nav-item">
    <a href="{{ url_for('admin.admin_dashboard') }}" class="nav-link {% if request.endpoint == 'admin.admin_dashboard' %}active{% endif %}">
        <i class="fas fa-tachometer-alt"></i>
        <span>Dashboard</span>
    </a>
</div>

<div class="nav-item">
    <a href="{{ url_for('admin.analytics') }}" class="nav-link {% if request.endpoint == 'admin.analytics' %}active{% endif %}">
        <i class="fas fa-chart-line"></i>
        <span>Analytics</span>
    </a>
</div>

<div class="nav-item">
    <a href="{{ url_for('admin.manage_students') }}" class="nav-link {% if 'student' in request.endpoint %}active{% endif %}">
        <i class="fas fa-user-graduate"></i>
        <span>Students</span>
    </a>
</div>

<div class="nav-item">
    <a href="{{ url_for('admin.manage_faculty') }}" class="nav-link {% if 'faculty' in request.endpoint %}active{% endif %}">
        <i class="fas fa-chalkboard-teacher"></i>
        <span>Faculty</span>
    </a>
</div>

<div class="nav-item">
    <a href="#" class="nav-link" onclick="toggleSubmenu(this)">
        <i class="fas fa-info-circle"></i>
        <span>College Info</span>
        <i class="fas fa-chevron-down ms-auto"></i>
    </a>
    <div class="submenu">
        <a href="{{ url_for('admin.manage_predefined_info') }}" class="nav-link">
            <i class="fas fa-edit"></i>
            <span class="submenu-text">Predefined Info</span>
        </a>
        <a href="{{ url_for('admin.manage_faqs') }}" class="nav-link">
            <i class="fas fa-question"></i>
            <span class="submenu-text">FAQ Management</span>
        </a>
    </div>
</div>

<div class="nav-item">
    <a href="#" class="nav-link" onclick="toggleSubmenu(this)">
        <i class="fas fa-bell"></i>
        <span>Notifications</span>
        <i class="fas fa-chevron-down ms-auto"></i>
    </a>
    <div class="submenu">
        <a href="{{ url_for('admin.create_notification') }}" class="nav-link">
            <i class="fas fa-plus"></i>
            <span class="submenu-text">Add Notification</span>
        </a>
        <a href="{{ url_for('admin.manage_notifications') }}" class="nav-link">
            <i class="fas fa-list"></i>
            <span class="submenu-text">View All</span>
        </a>
    </div>
</div>

<div class="nav-item">
    <a href="{{ url_for('admin.manage_complaints') }}" class="nav-link {% if 'complaint' in request.endpoint %}active{% endif %}">
        <i class="fas fa-exclamation-triangle"></i>
        <span>Complaints</span>
    </a>
</div>

<div class="nav-item">
    <a href="{{ url_for('accounts.students_fees_simple') }}" class="nav-link {% if 'accounts' in request.endpoint %}active{% endif %}">
        <i class="fas fa-users-cog"></i>
        <span>Accounts</span>
    </a>
</div>

<div class="nav-item">
    <a href="{{ url_for('auth.logout') }}" class="nav-link">
        <i class="fas fa-sign-out-alt"></i>
        <span>Logout</span>
    </a>
</div>
{% endblock %}'''
    
    # Fix 1: Update edit_student.html
    print("\n1. Fixing edit_student.html...")
    with open('app/templates/edit_student.html', 'r', encoding='utf-8') as f:
        student_content = f.read()
    
    # Add missing sidebar navigation
    old_student_start = '''{% extends "base_dashboard.html" %}

{% block title %}Edit Student - EduBot Admin{% endblock %}

{% block content %}'''
    
    new_student_start = '''{% extends "base_dashboard.html" %}

{% block title %}Edit Student - EduBot Admin{% endblock %}

''' + standard_sidebar + '''

{% block content %}'''
    
    student_content = student_content.replace(old_student_start, new_student_start)
    
    # Update action buttons to be consistent
    old_student_actions = '''                <div class="d-flex gap-2">
                    <a href="{{ url_for('admin.admin_dashboard') }}" class="btn btn-outline-info">
                        <i class="fas fa-tachometer-alt me-2"></i> Dashboard
                    </a>
                    <a href="{{ url_for('admin.manage_students') }}" class="btn btn-outline-secondary">
                        <i class="fas fa-list me-2"></i> Students
                    </a>
                </div>'''
    
    new_student_actions = '''                <div class="d-flex gap-2">
                    <button class="btn btn-outline-primary btn-sm" onclick="refreshPage()">
                        <i class="fas fa-sync-alt"></i> Refresh
                    </button>
                    <a href="{{ url_for('admin.admin_dashboard') }}" class="btn btn-outline-info">
                        <i class="fas fa-tachometer-alt me-2"></i> Dashboard
                    </a>
                    <a href="{{ url_for('admin.manage_students') }}" class="btn btn-outline-secondary">
                        <i class="fas fa-list me-2"></i> Students
                    </a>
                </div>'''
    
    student_content = student_content.replace(old_student_actions, new_student_actions)
    
    with open('app/templates/edit_student.html', 'w', encoding='utf-8') as f:
        f.write(student_content)
    
    # Fix 2: Update edit_faculty.html
    print("2. Fixing edit_faculty.html...")
    with open('app/templates/edit_faculty.html', 'r', encoding='utf-8') as f:
        faculty_content = f.read()
    
    # Add missing sidebar navigation
    old_faculty_start = '''{% extends "base_dashboard.html" %}

{% block title %}Edit Faculty - EduBot Admin{% endblock %}

{% block content %}'''
    
    new_faculty_start = '''{% extends "base_dashboard.html" %}

{% block title %}Edit Faculty - EduBot Admin{% endblock %}

''' + standard_sidebar + '''

{% block content %}'''
    
    faculty_content = faculty_content.replace(old_faculty_start, new_faculty_start)
    
    # Update action buttons to be consistent
    old_faculty_actions = '''                <div class="d-flex gap-2">
                    <a href="{{ url_for('admin.admin_dashboard') }}" class="btn btn-outline-info">
                        <i class="fas fa-tachometer-alt me-2"></i> Dashboard
                    </a>
                    <a href="{{ url_for('admin.manage_faculty') }}" class="btn btn-outline-secondary">
                        <i class="fas fa-list me-2"></i> Faculty
                    </a>
                </div>'''
    
    new_faculty_actions = '''                <div class="d-flex gap-2">
                    <button class="btn btn-outline-primary btn-sm" onclick="refreshPage()">
                        <i class="fas fa-sync-alt"></i> Refresh
                    </button>
                    <a href="{{ url_for('admin.admin_dashboard') }}" class="btn btn-outline-info">
                        <i class="fas fa-tachometer-alt me-2"></i> Dashboard
                    </a>
                    <a href="{{ url_for('admin.manage_faculty') }}" class="btn btn-outline-secondary">
                        <i class="fas fa-list me-2"></i> Faculty
                    </a>
                </div>'''
    
    faculty_content = faculty_content.replace(old_faculty_actions, new_faculty_actions)
    
    with open('app/templates/edit_faculty.html', 'w', encoding='utf-8') as f:
        f.write(faculty_content)
    
    # Fix 3: Add JavaScript functions to both templates
    print("3. Adding JavaScript functions...")
    
    standard_js = '''
<script>
function refreshPage() {
    window.location.reload();
}

// Initialize tooltips
document.addEventListener('DOMContentLoaded', () => {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
</script>'''
    
    # Add JavaScript to edit_student.html
    with open('app/templates/edit_student.html', 'r', encoding='utf-8') as f:
        student_content = f.read()
    
    if '<script>' not in student_content and student_content.endswith('</html>'):
        student_content = student_content.replace('</html>', standard_js + '</html>')
        with open('app/templates/edit_student.html', 'w', encoding='utf-8') as f:
            f.write(student_content)
    
    # Add JavaScript to edit_faculty.html
    with open('app/templates/edit_faculty.html', 'r', encoding='utf-8') as f:
        faculty_content = f.read()
    
    if '<script>' not in faculty_content and faculty_content.endswith('</html>'):
        faculty_content = faculty_content.replace('</html>', standard_js + '</html>')
        with open('app/templates/edit_faculty.html', 'w', encoding='utf-8') as f:
            f.write(faculty_content)
    
    print("\n=== FIX COMPLETE ===")
    print("\nChanges made:")
    print("1. Added consistent sidebar navigation to edit_student.html")
    print("2. Added consistent sidebar navigation to edit_faculty.html")
    print("3. Updated action buttons to include Refresh button")
    print("4. Added standard JavaScript functions")
    print("5. Ensured navigation highlights current section")
    print("\nBoth edit templates now use the same consistent sidebar navigation!")

if __name__ == "__main__":
    fix_edit_templates_navigation()
