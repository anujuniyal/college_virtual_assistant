#!/usr/bin/env python3
"""
Fix the persistent notification loading error when switching features
"""

def fix_notification_navigation_error_final():
    """Fix the notification JavaScript that continues running when navigating away"""
    
    print("=== FIXING NOTIFICATION NAVIGATION ERROR ===")
    
    with open('app/templates/notifications.html', 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Replace the entire JavaScript section with a cleaner version
    old_javascript = '''    <script>
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
    
    new_javascript = '''    <script>
    // Real-time notifications data management
    let notificationsData = [];
    let refreshInterval = null;
    let isNotificationsPage = false;
    let eventListenersAdded = false;
    
    // Initialize notifications page
    document.addEventListener('DOMContentLoaded', () => {
        // Check if we're actually on the notifications page
        if (window.location.pathname.includes('/notifications') && document.querySelector('.col-md-10')) {
            isNotificationsPage = true;
            startRealTimeUpdates();
            setupEventListeners();
        }
    });
    
    function setupEventListeners() {
        if (eventListenersAdded) return;
        eventListenersAdded = true;
        
        // Listen for visibility changes to pause/resume updates
        document.addEventListener('visibilitychange', handleVisibilityChange);
        
        // Listen for page unload to clean up
        window.addEventListener('beforeunload', handlePageUnload);
        
        // Listen for navigation changes
        window.addEventListener('popstate', handleNavigationChange);
        
        // Listen for SPA navigation (if using any frontend framework)
        window.addEventListener('hashchange', handleNavigationChange);
    }
    
    function handleVisibilityChange() {
        if (!isNotificationsPage) return;
        
        if (document.hidden) {
            stopRealTimeUpdates();
        } else {
            // Check if we're still on notifications page before resuming
            if (window.location.pathname.includes('/notifications') && document.querySelector('.col-md-10')) {
                startRealTimeUpdates();
            } else {
                cleanupAndStop();
            }
        }
    }
    
    function handlePageUnload() {
        cleanupAndStop();
    }
    
    function handleNavigationChange() {
        if (!window.location.pathname.includes('/notifications')) {
            cleanupAndStop();
        }
    }
    
    function cleanupAndStop() {
        stopRealTimeUpdates();
        isNotificationsPage = false;
        
        // Remove event listeners to prevent memory leaks
        if (eventListenersAdded) {
            document.removeEventListener('visibilitychange', handleVisibilityChange);
            window.removeEventListener('beforeunload', handlePageUnload);
            window.removeEventListener('popstate', handleNavigationChange);
            window.removeEventListener('hashchange', handleNavigationChange);
            eventListenersAdded = false;
        }
    }
    
    function startRealTimeUpdates() {
        // Clear existing interval
        stopRealTimeUpdates();
        
        // Only proceed if we're on notifications page
        if (!window.location.pathname.includes('/notifications') || !document.querySelector('.col-md-10')) {
            cleanupAndStop();
            return;
        }
        
        // Fetch initial data
        fetchNotifications();
        
        // Set up auto-refresh every 30 seconds
        refreshInterval = setInterval(() => {
            // Double-check we're still on notifications page before fetching
            if (isNotificationsPage && window.location.pathname.includes('/notifications') && document.querySelector('.col-md-10')) {
                fetchNotifications();
            } else {
                cleanupAndStop();
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
        if (!isNotificationsPage || !window.location.pathname.includes('/notifications') || !document.querySelector('.col-md-10')) {
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
                if (!isNotificationsPage || !window.location.pathname.includes('/notifications') || !document.querySelector('.col-md-10')) {
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
                // Only log errors if we're still on the notifications page
                if (isNotificationsPage && window.location.pathname.includes('/notifications')) {
                    console.log('Error fetching notifications:', error);
                }
            });
    }'''
    
    template_content = template_content.replace(old_javascript, new_javascript)
    
    # Also update the showUpdateIndicator function to be more robust
    old_indicator = '''    function showUpdateIndicator() {
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
    }'''
    
    new_indicator = '''    function showUpdateIndicator() {
        // Only show indicator if we're still on notifications page
        if (!isNotificationsPage || !window.location.pathname.includes('/notifications') || !document.querySelector('.col-md-10')) {
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
            if (indicator.parentNode) {
                indicator.style.animation = 'slideOutRight 0.3s ease';
                setTimeout(() => {
                    if (indicator.parentNode) {
                        indicator.remove();
                    }
                }, 300);
            }
        }, 3000);
    }'''
    
    template_content = template_content.replace(old_indicator, new_indicator)
    
    with open('app/templates/notifications.html', 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    print("\n=== FIX COMPLETE ===")
    print("\nChanges made:")
    print("1. Improved page detection using window.location.pathname")
    print("2. Added proper event listener cleanup")
    print("3. Enhanced navigation change handling")
    print("4. Added memory leak prevention")
    print("5. Improved error handling for navigation away")
    print("6. Made indicator function more robust")
    print("\nThe notification error when switching features should now be resolved!")

if __name__ == "__main__":
    fix_notification_navigation_error_final()
