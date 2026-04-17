#!/usr/bin/env python3
"""
Fix notification loading error when switching between features
"""

def fix_notifications_navigation_error():
    """Fix the JavaScript error when navigating away from notifications page"""
    
    with open('app/templates/notifications.html', 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Fix 1: Improve JavaScript to handle page navigation properly
    old_javascript = '''    <script>
    // Real-time notifications data management
    let notificationsData = [];
    let refreshInterval;
    
    // Initialize notifications page
    document.addEventListener('DOMContentLoaded', () => {
        startRealTimeUpdates();
        setupEventListeners();
    });
    
    function setupEventListeners() {
        // Listen for visibility changes to pause/resume updates
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                stopRealTimeUpdates();
            } else {
                startRealTimeUpdates();
            }
        });
    }
    
    function startRealTimeUpdates() {
        // Clear existing interval
        stopRealTimeUpdates();
        
        // Fetch initial data
        fetchNotifications();
        
        // Set up auto-refresh every 30 seconds
        refreshInterval = setInterval(fetchNotifications, 30000);
    }
    
    function stopRealTimeUpdates() {
        if (refreshInterval) {
            clearInterval(refreshInterval);
            refreshInterval = null;
        }
    }
    
    function fetchNotifications() {
        fetch('/api/notifications-realtime')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateNotificationsDisplay(data.notifications);
                    showUpdateIndicator();
                }
            })
            .catch(error => {
                console.log('Error fetching notifications:', error);
            });
    }'''
    
    new_javascript = '''    <script>
    // Real-time notifications data management
    let notificationsData = [];
    let refreshInterval;
    let isNotificationsPage = true;
    
    // Initialize notifications page
    document.addEventListener('DOMContentLoaded', () => {
        // Check if we're still on the notifications page
        if (document.querySelector('.col-md-10')) {
            startRealTimeUpdates();
            setupEventListeners();
        }
    });
    
    function setupEventListeners() {
        // Listen for visibility changes to pause/resume updates
        document.addEventListener('visibilitychange', () => {
            if (!isNotificationsPage) return;
            
            if (document.hidden) {
                stopRealTimeUpdates();
            } else {
                // Check if we're still on notifications page before resuming
                if (document.querySelector('.col-md-10')) {
                    startRealTimeUpdates();
                }
            }
        });
        
        // Listen for page unload to clean up
        window.addEventListener('beforeunload', () => {
            stopRealTimeUpdates();
            isNotificationsPage = false;
        });
        
        // Listen for navigation changes
        window.addEventListener('popstate', () => {
            if (!window.location.pathname.includes('/notifications')) {
                stopRealTimeUpdates();
                isNotificationsPage = false;
            }
        });
    }
    
    function startRealTimeUpdates() {
        // Clear existing interval
        stopRealTimeUpdates();
        
        // Only proceed if we're on notifications page
        if (!document.querySelector('.col-md-10')) {
            isNotificationsPage = false;
            return;
        }
        
        isNotificationsPage = true;
        
        // Fetch initial data
        fetchNotifications();
        
        // Set up auto-refresh every 30 seconds
        refreshInterval = setInterval(() => {
            // Double-check we're still on notifications page before fetching
            if (isNotificationsPage && document.querySelector('.col-md-10')) {
                fetchNotifications();
            } else {
                stopRealTimeUpdates();
            }
        }, 30000);
    }
    
    function stopRealTimeUpdates() {
        if (refreshInterval) {
            clearInterval(refreshInterval);
            refreshInterval = null;
        }
    }
    
    function fetchNotifications() {
        // Only fetch if we're still on notifications page
        if (!isNotificationsPage || !document.querySelector('.col-md-10')) {
            return;
        }
        
        fetch('/api/notifications-realtime')
            .then(response => {
                // Check if we're still on notifications page
                if (!isNotificationsPage) {
                    throw new Error('Navigated away from notifications page');
                }
                return response.json();
            })
            .then(data => {
                // Final check before updating DOM
                if (!isNotificationsPage || !document.querySelector('.col-md-10')) {
                    return;
                }
                
                if (data.success) {
                    updateNotificationsDisplay(data.notifications);
                    showUpdateIndicator();
                } else {
                    console.log('API returned error:', data.message);
                }
            })
            .catch(error => {
                // Don't log errors when navigating away (expected behavior)
                if (isNotificationsPage) {
                    console.log('Error fetching notifications:', error);
                }
            });
    }'''
    
    template_content = template_content.replace(old_javascript, new_javascript)
    
    # Fix 2: Add better error handling and cleanup
    old_update_function = '''    function updateNotificationsDisplay(notifications) {
        const container = document.querySelector('.col-md-10');
        if (!container) return;'''
    
    new_update_function = '''    function updateNotificationsDisplay(notifications) {
        const container = document.querySelector('.col-md-10');
        if (!container) {
            isNotificationsPage = false;
            stopRealTimeUpdates();
            return;
        }'''
    
    template_content = template_content.replace(old_update_function, new_update_function)
    
    # Fix 3: Add page detection helper
    old_show_indicator = '''    function showUpdateIndicator() {
        // Show subtle indicator that data was updated
        const indicator = document.createElement('div');
        indicator.className = 'update-indicator';
        indicator.innerHTML = '<i class="fas fa-check-circle"></i> Notifications updated';
        indicator.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #28a745;
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            font-size: 0.9rem;
            z-index: 1000;
            animation: slideInRight 0.3s ease;
        `;
        
        document.body.appendChild(indicator);
        
        setTimeout(() => {
            indicator.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => indicator.remove(), 300);
        }, 3000);
    }'''
    
    new_show_indicator = '''    function showUpdateIndicator() {
        // Only show indicator if we're still on notifications page
        if (!isNotificationsPage || !document.querySelector('.col-md-10')) {
            return;
        }
        
        // Show subtle indicator that data was updated
        const indicator = document.createElement('div');
        indicator.className = 'update-indicator';
        indicator.innerHTML = '<i class="fas fa-check-circle"></i> Notifications updated';
        indicator.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #28a745;
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            font-size: 0.9rem;
            z-index: 1000;
            animation: slideInRight 0.3s ease;
        `;
        
        document.body.appendChild(indicator);
        
        setTimeout(() => {
            indicator.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => indicator.remove(), 300);
        }, 3000);
    }
    
    // Helper function to check if we're on notifications page
    function isOnNotificationsPage() {
        return window.location.pathname.includes('/notifications') && 
               document.querySelector('.col-md-10') !== null;
    }'''
    
    template_content = template_content.replace(old_show_indicator, new_show_indicator)
    
    # Fix 4: Update the session user role assignment to be more robust
    old_session_assignment = '''    // Store session data for JavaScript access
    window.sessionUserRole = '{{ session.user_role }}';'''
    
    new_session_assignment = '''    // Store session data for JavaScript access
    window.sessionUserRole = '{{ session.user_role|default if session.user_role else "" }}';'''
    
    template_content = template_content.replace(old_session_assignment, new_session_assignment)
    
    with open('app/templates/notifications.html', 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    print("Fixed notifications navigation error!")
    print("\nChanges made:")
    print("1. Added page detection to prevent fetching when not on notifications page")
    print("2. Added proper cleanup when navigating away from notifications")
    print("3. Added beforeunload and popstate event listeners")
    print("4. Improved error handling to ignore expected navigation errors")
    print("5. Added double-checking before DOM updates")
    print("6. Enhanced session data handling")
    print("\nThe notification error when switching features should now be resolved!")

if __name__ == "__main__":
    fix_notifications_navigation_error()
