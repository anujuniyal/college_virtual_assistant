#!/usr/bin/env python3
"""
Fix notifications.html to use real-time data
"""

def fix_notifications_realtime():
    """Update notifications.html template to use real-time data"""
    
    with open('app/templates/notifications.html', 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Fix 1: Add real-time data refresh functionality
    old_script = '''    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''
    
    new_script = '''    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    
    <script>
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
    }
    
    function updateNotificationsDisplay(notifications) {
        const container = document.querySelector('.col-md-10');
        if (!container) return;
        
        // Get current notifications HTML structure
        const notificationsHTML = notifications.map(notification => {
            const createdDate = new Date(notification.created_at);
            const formattedDate = createdDate.toLocaleDateString('en-US', {
                day: 'numeric',
                month: 'short',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
            
            const expiresDate = notification.expires_at ? new Date(notification.expires_at) : null;
            const expiresFormatted = expiresDate ? expiresDate.toLocaleDateString('en-US', {
                day: 'numeric',
                month: 'short',
                year: 'numeric'
            }) : '';
            
            const isActive = !notification.expires_at || new Date(notification.expires_at) > new Date();
            const statusBadge = isActive ? 
                '<span class="badge bg-success">Active</span>' : 
                '<span class="badge bg-secondary">Expired</span>';
            
            const priorityBadge = notification.priority === 'high' ? 
                '<span class="badge bg-danger">High Priority</span>' : 
                '<span class="badge bg-primary">Normal Priority</span>';
            
            return `
                <div class="notification-card" data-notification-id="${notification.id}">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <div class="d-flex align-items-center mb-2">
                                <h5 class="mb-0 me-3">${notification.title}</h5>
                                <small class="text-muted">
                                    <i class="bi bi-person-circle"></i> ${notification.created_by_name || 'System'}
                                </small>
                            </div>
                            
                            <small class="text-muted d-block mb-2">
                                <i class="bi bi-clock"></i> ${formattedDate}
                                ${expiresFormatted ? `| <i class="bi bi-calendar-x"></i> Expires: ${expiresFormatted}` : ''}
                            </small>
                            
                            <div class="mb-3">
                                <small>
                                    ${priorityBadge}
                                    ${statusBadge}
                                    <span class="badge bg-info">Target: All</span>
                                </small>
                            </div>
                            
                            <p class="mb-3">${notification.content}</p>
                            
                            ${notification.link_url ? `
                                <a href="${notification.link_url}" target="_blank" class="btn btn-sm btn-outline-primary me-2">
                                    <i class="bi bi-link-45deg"></i> View Link
                                </a>
                            ` : ''}
                            
                            ${notification.file_url ? `
                                <a href="${notification.file_url}" target="_blank" class="btn btn-sm btn-outline-secondary me-2">
                                    <i class="bi bi-file-earmark"></i> View File
                                </a>
                            ` : ''}
                        </div>
                        <div class="dropdown">
                            <button class="btn btn-sm btn-outline-secondary" type="button" data-bs-toggle="dropdown">
                                <i class="bi bi-three-dots-vertical"></i>
                            </button>
                            <ul class="dropdown-menu">
                                ${window.sessionUserRole === 'admin' ? `
                                    <li><a class="dropdown-item" href="/edit-notification/${notification.id}">
                                        <i class="bi bi-pencil"></i> Edit
                                    </a></li>
                                    <li><a class="dropdown-item text-danger" href="/delete-notification/${notification.id}" onclick="return confirm('Are you sure you want to delete this notification?')">
                                        <i class="bi bi-trash"></i> Delete
                                    </a></li>
                                ` : `
                                    <li><a class="dropdown-item disabled" href="#" title="Only admins can edit notifications">
                                        <i class="bi bi-pencil"></i> Edit (Admin Only)
                                    </a></li>
                                    <li><a class="dropdown-item disabled" href="#" title="Only admins can delete notifications">
                                        <i class="bi bi-trash"></i> Delete (Admin Only)
                                    </a></li>
                                `}
                            </ul>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        // Update the notifications container
        const notificationsContainer = container.querySelector('.d-flex.justify-content-between.align-items-center').nextElementSibling;
        if (notificationsContainer) {
            if (notifications.length > 0) {
                notificationsContainer.innerHTML = notificationsHTML;
            } else {
                notificationsContainer.innerHTML = `
                    <div class="text-center py-5">
                        <i class="bi bi-bell-slash" style="font-size: 4rem; color: #ccc;"></i>
                        <h5 class="mt-3">No Notifications</h5>
                        <p class="text-muted">Start by adding your first notification.</p>
                        ${window.sessionUserRole === 'admin' ? `
                            <a href="/create-notification" class="btn btn-primary">
                                <i class="bi bi-plus-circle"></i> Add First Notification
                            </a>
                        ` : ''}
                    </div>
                `;
            }
        }
    }
    
    function showUpdateIndicator() {
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
    
    // Add CSS animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideInRight {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        @keyframes slideOutRight {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
        
        .notification-card {
            transition: all 0.3s ease;
            border-left: 4px solid transparent;
        }
        
        .notification-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            border-left-color: #007bff;
        }
        
        .update-indicator {
            animation: slideInRight 0.3s ease;
        }
    `;
    document.head.appendChild(style);
    
    // Store session data for JavaScript access
    window.sessionUserRole = '{{ session.user_role }}';
    </script>
</body>
</html>'''
    
    template_content = template_content.replace(old_script, new_script)
    
    # Fix 2: Add manual refresh button
    old_header = '''                <div class="d-flex justify-content-between align-items-center mb-4">
                    <div>
                        <h2 class="mb-1">ð Digital Notice Board</h2>
                        <small class="text-muted">EduBot for Management Announcements</small>
                    </div>
                    <div>
                        <span class="badge bg-primary">{{ session.user_role|title }}</span>
                        <span class="text-muted">{{ session.user_name }}</span>
                    </div>
                </div>'''
    
    new_header = '''                <div class="d-flex justify-content-between align-items-center mb-4">
                    <div>
                        <h2 class="mb-1">ð Digital Notice Board</h2>
                        <small class="text-muted">EduBot for Management Announcements</small>
                    </div>
                    <div class="d-flex align-items-center gap-2">
                        <button class="btn btn-outline-primary btn-sm" onclick="fetchNotifications()" title="Refresh Notifications">
                            <i class="fas fa-sync-alt"></i> Refresh
                        </button>
                        <span class="badge bg-primary">{{ session.user_role|title }}</span>
                        <span class="text-muted">{{ session.user_name }}</span>
                    </div>
                </div>'''
    
    template_content = template_content.replace(old_header, new_header)
    
    with open('app/templates/notifications.html', 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    # Fix 3: Add API endpoint for real-time notifications data
    with open('app/routes.py', 'r', encoding='utf-8') as f:
        routes_content = f.read()
    
    # Add the API endpoint after the existing notifications route
    old_notifications_route = '''    @app.route('/notifications')
    @login_required
    def notifications_dashboard():
        """Notifications dashboard"""
        # Get all notifications with author info
        notifications = db.session.query(Notification, Admin).outerjoin(Admin, Notification.created_by == Admin.id).order_by(Notification.created_at.desc()).all()
        
        return render_template('notifications.html', notifications=notifications)'''
    
    new_notifications_route = '''    @app.route('/notifications')
    @login_required
    def notifications_dashboard():
        """Notifications dashboard"""
        # Get all notifications with author info
        notifications = db.session.query(Notification, Admin).outerjoin(Admin, Notification.created_by == Admin.id).order_by(Notification.created_at.desc()).all()
        
        return render_template('notifications.html', notifications=notifications)
    
    @app.route('/api/notifications-realtime')
    @login_required
    def notifications_realtime():
        """API endpoint for real-time notifications data"""
        try:
            # Get all notifications with author info
            notifications_data = db.session.query(Notification, Admin).outerjoin(Admin, Notification.created_by == Admin.id).order_by(Notification.created_at.desc()).all()
            
            notifications_list = []
            for notification, admin in notifications_data:
                notifications_list.append({
                    'id': notification.id,
                    'title': notification.title,
                    'content': notification.content,
                    'link_url': notification.link_url,
                    'file_url': notification.file_url,
                    'priority': notification.priority,
                    'created_at': notification.created_at.isoformat() if notification.created_at else None,
                    'expires_at': notification.expires_at.isoformat() if notification.expires_at else None,
                    'created_by_name': admin.name if admin else 'System',
                    'notification_type': notification.notification_type
                })
            
            return jsonify({
                'success': True,
                'notifications': notifications_list,
                'count': len(notifications_list)
            })
            
        except Exception as e:
            current_app.logger.error(f"Error fetching real-time notifications: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Error loading notifications',
                'notifications': []
            }), 500'''
    
    routes_content = routes_content.replace(old_notifications_route, new_notifications_route)
    
    with open('app/routes.py', 'w', encoding='utf-8') as f:
        f.write(routes_content)
    
    print("Fixed notifications.html to use real-time data!")
    print("\nChanges made:")
    print("1. Added real-time data fetching with auto-refresh every 30 seconds")
    print("2. Added manual refresh button")
    print("3. Added API endpoint for real-time notifications data")
    print("4. Added visual update indicators")
    print("5. Enhanced notification cards with hover effects")
    print("6. Added pause/resume based on page visibility")
    print("\nThe notifications view will now update automatically with real-time data!")

if __name__ == "__main__":
    fix_notifications_realtime()
