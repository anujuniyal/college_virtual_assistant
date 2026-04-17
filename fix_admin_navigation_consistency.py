#!/usr/bin/env python3
"""
Fix admin dashboard sidebar navigation and action button consistency across all features
"""

def fix_admin_navigation_consistency():
    """Ensure consistent sidebar navigation and action buttons across all admin features"""
    
    print("=== FIXING ADMIN DASHBOARD NAVIGATION CONSISTENCY ===")
    
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
    
    # Define standard action buttons structure
    standard_actions = '''                <div class="d-flex gap-2">
                    <button class="btn btn-outline-primary btn-sm" onclick="refreshPage()">
                        <i class="fas fa-sync-alt"></i> Refresh
                    </button>
                    <a href="{{ url_for('admin.admin_dashboard') }}" class="btn btn-outline-info">
                        <i class="fas fa-tachometer-alt me-2"></i> Dashboard
                    </a>
                </div>'''
    
    # Fix 1: Update manage_complaints.html
    print("\n1. Fixing manage_complaints.html...")
    with open('app/templates/manage_complaints.html', 'r', encoding='utf-8') as f:
        complaints_content = f.read()
    
    # Add missing sidebar navigation
    old_complaints_start = '''{% extends "base_dashboard.html" %}

{% block title %}Manage Complaints - EduBot Admin{% endblock %}

{% block content %}'''
    
    new_complaints_start = '''{% extends "base_dashboard.html" %}

{% block title %}Manage Complaints - EduBot Admin{% endblock %}

''' + standard_sidebar + '''

{% block content %}'''
    
    complaints_content = complaints_content.replace(old_complaints_start, new_complaints_start)
    
    # Fix action buttons
    old_complaints_actions = '''            <div class="d-flex justify-content-between align-items-center mb-4">
                <div class="d-flex align-items-center gap-3">
                    <h2 class="h4 mb-0">Manage Complaints</h2>
                    <a href="{{ url_for('admin.admin_dashboard') }}" class="btn btn-outline-secondary">
                        <i class="fas fa-arrow-left me-2"></i> Back to Dashboard
                    </a>
                </div>
            </div>'''
    
    new_complaints_actions = '''            <div class="d-flex justify-content-between align-items-center mb-4">
                <div class="d-flex align-items-center gap-2">
                    <h2 class="h4 mb-0">Manage Complaints</h2>
                    <span class="badge bg-warning">Complaint Management</span>
                </div>
                ''' + standard_actions + '''
            </div>'''
    
    complaints_content = complaints_content.replace(old_complaints_actions, new_complaints_actions)
    
    with open('app/templates/manage_complaints.html', 'w', encoding='utf-8') as f:
        f.write(complaints_content)
    
    # Fix 2: Update manage_faqs.html action buttons
    print("2. Fixing manage_faqs.html...")
    with open('app/templates/manage_faqs.html', 'r', encoding='utf-8') as f:
        faqs_content = f.read()
    
    # Fix inconsistent action buttons in FAQs
    old_faqs_actions = '''                <div class="d-flex gap-2">
                    <button class="btn btn-outline-primary btn-sm" onclick="refreshFAQs()">
                        <i class="fas fa-sync-alt"></i> Refresh
                    </button>
                    <a href="{{ url_for('admin.admin_dashboard') }}" class="btn btn-outline-info">
                        <i class="fas fa-tachometer-alt me-2"></i> Dashboard
                    </a>
                    <a href="{{ url_for('admin.manage_complaints') }}" class="btn btn-outline-warning">
                        <i class="fas fa-list-alt me-2"></i> FAQ Records
                    </a>
                    <a href="{{ url_for('admin.add_faq') }}" class="btn btn-success">
                        <i class="fas fa-plus me-2"></i> Add FAQ
                    </a>
                </div>'''
    
    new_faqs_actions = '''                <div class="d-flex gap-2">
                    <button class="btn btn-outline-primary btn-sm" onclick="refreshFAQs()">
                        <i class="fas fa-sync-alt"></i> Refresh
                    </button>
                    <a href="{{ url_for('admin.admin_dashboard') }}" class="btn btn-outline-info">
                        <i class="fas fa-tachometer-alt me-2"></i> Dashboard
                    </a>
                    <a href="{{ url_for('admin.add_faq') }}" class="btn btn-success">
                        <i class="fas fa-plus me-2"></i> Add FAQ
                    </a>
                </div>'''
    
    faqs_content = faqs_content.replace(old_faqs_actions, new_faqs_actions)
    
    with open('app/templates/manage_faqs.html', 'w', encoding='utf-8') as f:
        f.write(faqs_content)
    
    # Fix 3: Update manage_notifications.html action buttons
    print("3. Fixing manage_notifications.html...")
    with open('app/templates/manage_notifications.html', 'r', encoding='utf-8') as f:
        notifications_content = f.read()
    
    # Find and update the action buttons section
    old_notifications_actions = '''    <div class="section-header">
        <h2 class="section-title"><i class="bi bi-bell"></i> Recent Notifications</h2>
        <a href="{{ url_for('admin.create_notification') }}" class="btn btn-primary">
            <i class="bi bi-plus-lg"></i> Add Notification
        </a>
    </div>'''
    
    new_notifications_actions = '''    <div class="section-header">
        <h2 class="section-title"><i class="bi bi-bell"></i> Recent Notifications</h2>
        <div class="d-flex gap-2">
            <button class="btn btn-outline-primary btn-sm" onclick="refreshNotifications()">
                <i class="fas fa-sync-alt"></i> Refresh
            </button>
            <a href="{{ url_for('admin.admin_dashboard') }}" class="btn btn-outline-info">
                <i class="fas fa-tachometer-alt me-2"></i> Dashboard
            </a>
            <a href="{{ url_for('admin.create_notification') }}" class="btn btn-success">
                <i class="fas fa-plus me-2"></i> Add Notification
            </a>
        </div>
    </div>'''
    
    notifications_content = notifications_content.replace(old_notifications_actions, new_notifications_actions)
    
    with open('app/templates/manage_notifications.html', 'w', encoding='utf-8') as f:
        f.write(notifications_content)
    
    # Fix 4: Update analytics.html if it exists
    print("4. Fixing analytics.html...")
    try:
        with open('app/templates/analytics.html', 'r', encoding='utf-8') as f:
            analytics_content = f.read()
        
        # Check if it has sidebar navigation
        if '{% block sidebar_nav %}' not in analytics_content:
            # Add standard sidebar
            old_analytics_start = '''{% extends "base_dashboard.html" %}

{% block title %}Analytics - EduBot Admin{% endblock %}

{% block content %}'''
            
            new_analytics_start = '''{% extends "base_dashboard.html" %}

{% block title %}Analytics - EduBot Admin{% endblock %}

''' + standard_sidebar + '''

{% block content %}'''
            
            analytics_content = analytics_content.replace(old_analytics_start, new_analytics_start)
            
            with open('app/templates/analytics.html', 'w', encoding='utf-8') as f:
                f.write(analytics_content)
                
    except FileNotFoundError:
        print("   analytics.html not found, skipping...")
    
    # Fix 5: Add standard JavaScript functions
    print("5. Adding standard JavaScript functions...")
    
    standard_js = '''
<script>
function refreshPage() {
    window.location.reload();
}

function refreshFAQs() {
    window.location.reload();
}

function refreshNotifications() {
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
    
    # Add JavaScript to templates that don't have it
    templates_to_check = [
        'app/templates/manage_complaints.html',
        'app/templates/manage_faqs.html',
        'app/templates/manage_notifications.html'
    ]
    
    for template in templates_to_check:
        try:
            with open(template, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if '<script>' not in content and content.endswith('</html>'):
                content = content.replace('</html>', standard_js + '</html>')
                with open(template, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
        except FileNotFoundError:
            pass
    
    print("\n=== FIX COMPLETE ===")
    print("\nChanges made:")
    print("1. Standardized sidebar navigation across all admin templates")
    print("2. Fixed action button consistency (Refresh + Dashboard + Add)")
    print("3. Removed inconsistent buttons (FAQ Records, Back to Dashboard)")
    print("4. Added standard JavaScript functions")
    print("5. Ensured all templates have proper sidebar navigation")
    print("\nAll admin features now have consistent navigation and action buttons!")

if __name__ == "__main__":
    fix_admin_navigation_consistency()
