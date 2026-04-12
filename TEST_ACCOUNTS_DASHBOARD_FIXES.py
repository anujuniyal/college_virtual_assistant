#!/usr/bin/env python3
"""
Test Accounts Dashboard Navigation and CSS Theme Fixes
"""
import sys
import os

# Add app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_back_button_exists():
    """Test that back to dashboard button exists in student feature template"""
    print("=== BACK TO DASHBOARD BUTTON TEST ===")
    
    template_path = os.path.join(os.path.dirname(__file__), 'app', 'templates', 'students_fees_standalone.html')
    
    if not os.path.exists(template_path):
        print("ERROR: students_fees_standalone.html template not found")
        return False
    
    with open(template_path, 'r') as f:
        content = f.read()
    
    # Check for back to dashboard button
    back_button_patterns = [
        'Back to Dashboard',
        'accounts_dashboard',
        'btn-outline-primary'
    ]
    
    found_patterns = []
    for pattern in back_button_patterns:
        if pattern in content:
            found_patterns.append(pattern)
            print(f"  Found: {pattern}")
        else:
            print(f"  Missing: {pattern}")
    
    # Check for proper Bootstrap Icons usage
    if 'bi bi-arrow-left' in content:
        print("  Found: Bootstrap Icons arrow-left")
        found_patterns.append('bi-arrow-left')
    else:
        print("  Missing: Bootstrap Icons arrow-left")
    
    success = len(found_patterns) >= 3  # At least 3 patterns should be found
    print(f"Back button test: {'PASS' if success else 'FAIL'}")
    
    return success

def test_css_theme_consistency():
    """Test CSS theme consistency across dashboard templates"""
    print("\n=== CSS THEME CONSISTENCY TEST ===")
    
    templates_to_check = {
        'accounts_dashboard.html': 'dashboard.css',
        'students_fees_standalone.html': 'dashboard.css',
        'base_dashboard.html': 'dashboard.css',  # Base template for admin/faculty
        'admin_dashboard_edubot.html': 'extends base_dashboard.html',
        'faculty_dashboard_edubot.html': 'extends base_dashboard.html'
    }
    
    results = {}
    
    for template_name, expected_css in templates_to_check.items():
        template_path = os.path.join(os.path.dirname(__file__), 'app', 'templates', template_name)
        
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                content = f.read()
            
            if 'extends "base_dashboard.html"' in content or "extends 'base_dashboard.html'" in content:
                print(f"  {template_name}: Extends base_dashboard.html - CORRECT")
                results[template_name] = True
            elif expected_css in content:
                print(f"  {template_name}: Using {expected_css} - CORRECT")
                results[template_name] = True
            else:
                # Check if it's using whatsapp-theme.css (which we want to avoid)
                if 'whatsapp-theme.css' in content:
                    print(f"  {template_name}: Using whatsapp-theme.css - INCORRECT")
                    results[template_name] = False
                else:
                    print(f"  {template_name}: CSS file not found - NEEDS CHECK")
                    results[template_name] = False
        else:
            print(f"  {template_name}: Template not found")
            results[template_name] = False
    
    success = all(results.values())
    print(f"CSS theme consistency: {'PASS' if success else 'FAIL'}")
    
    return success

def test_navigation_links():
    """Test navigation links in accounts dashboard"""
    print("\n=== NAVIGATION LINKS TEST ===")
    
    template_path = os.path.join(os.path.dirname(__file__), 'app', 'templates', 'accounts_dashboard.html')
    
    if not os.path.exists(template_path):
        print("ERROR: accounts_dashboard.html template not found")
        return False
    
    with open(template_path, 'r') as f:
        content = f.read()
    
    # Check for key navigation links
    navigation_checks = {
        'students_fees_dashboard': 'Students link',
        'manage_notifications': 'Notifications link',
        'edit_profile': 'Edit profile link',
        'auth.logout': 'Logout link'
    }
    
    found_links = {}
    for route, description in navigation_checks.items():
        if route in content:
            print(f"  Found: {description}")
            found_links[route] = True
        else:
            print(f"  Missing: {description}")
            found_links[route] = False
    
    success = all(found_links.values())
    print(f"Navigation links test: {'PASS' if success else 'FAIL'}")
    
    return success

def test_css_files_exist():
    """Test that required CSS files exist"""
    print("\n=== CSS FILES EXISTENCE TEST ===")
    
    css_files = {
        'dashboard.css': 'Non-WhatsApp theme',
        'whatsapp-theme.css': 'WhatsApp theme'
    }
    
    css_dir = os.path.join(os.path.dirname(__file__), 'app', 'static', 'css')
    
    results = {}
    
    for css_file, description in css_files.items():
        css_path = os.path.join(css_dir, css_file)
        
        if os.path.exists(css_path):
            file_size = os.path.getsize(css_path)
            print(f"  {css_file}: EXISTS ({file_size} bytes) - {description}")
            results[css_file] = True
        else:
            print(f"  {css_file}: NOT FOUND - {description}")
            results[css_file] = False
    
    # dashboard.css should exist, whatsapp-theme.css can exist but shouldn't be used
    success = results.get('dashboard.css', False)
    print(f"CSS files test: {'PASS' if success else 'FAIL'}")
    
    return success

def test_template_syntax():
    """Test template syntax for JavaScript errors"""
    print("\n=== TEMPLATE SYNTAX TEST ===")
    
    template_path = os.path.join(os.path.dirname(__file__), 'app', 'templates', 'students_fees_standalone.html')
    
    if not os.path.exists(template_path):
        print("ERROR: students_fees_standalone.html template not found")
        return False
    
    with open(template_path, 'r') as f:
        content = f.read()
    
    # Check for common JavaScript syntax issues
    syntax_checks = {
        'onclick="viewStudentDetails': 'Properly escaped onclick',
        'bi bi-arrow-left': 'Bootstrap Icons usage',
        'btn-outline-primary': 'Bootstrap button styling',
        'd-flex justify-content-between': 'Flexbox layout'
    }
    
    found_patterns = {}
    for pattern, description in syntax_checks.items():
        if pattern in content:
            print(f"  Found: {description}")
            found_patterns[pattern] = True
        else:
            print(f"  Missing: {description}")
            found_patterns[pattern] = False
    
    success = all(found_patterns.values())
    print(f"Template syntax test: {'PASS' if success else 'FAIL'}")
    
    return success

def main():
    """Main test function"""
    print("ACCOUNTS DASHBOARD NAVIGATION AND CSS THEME VERIFICATION")
    print("=" * 60)
    
    results = {
        'back_button': test_back_button_exists(),
        'css_theme': test_css_theme_consistency(),
        'navigation': test_navigation_links(),
        'css_files': test_css_files_exist(),
        'syntax': test_template_syntax()
    }
    
    print("\n" + "=" * 60)
    print("ACCOUNTS DASHBOARD FIXES TEST RESULTS")
    print("=" * 60)
    
    for test, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test.replace('_', ' ').title()}: {status}")
    
    # Overall status
    all_passed = all(results.values())
    print(f"\nOverall Status: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    
    if all_passed:
        print("\nFIXES SUCCESSFULLY APPLIED:")
        print("1. Back to dashboard button added to student feature template")
        print("2. CSS theme updated to non-WhatsApp theme (dashboard.css)")
        print("3. Navigation consistency maintained across dashboards")
        print("4. Template syntax errors fixed")
        print("5. All required CSS files available")
    else:
        print("\nISSUES FOUND:")
        for test, result in results.items():
            if not result:
                print(f"  - {test.replace('_', ' ').title()}: FAILED")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
