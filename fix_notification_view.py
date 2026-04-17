#!/usr/bin/env python3
"""
Fix notification view feature loading issue
"""

def fix_notification_view():
    """Fix notification view loading issues"""
    
    # Fix 1: Add missing view_notifications route to admin blueprint
    with open('app/blueprints/admin.py', 'r', encoding='utf-8') as f:
        admin_content = f.read()
    
    # Add the missing view_notifications route
    missing_route = '''

@admin_bp.route('/view-notifications')
@login_required
@admin_required
def view_notifications():
    """View all notifications - separate route for better organization"""
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = 20
        search = request.args.get('search', '')
        status_filter = request.args.get('status', '')
        
        # Build query
        query = Notification.query
        
        # Apply search filter
        if search:
            query = query.filter(
                Notification.title.ilike(f'%{search}%') |
                Notification.content.ilike(f'%{search}%')
            )
        
        # Apply status filter
        if status_filter == 'active':
            query = query.filter(Notification.expires_at > datetime.utcnow())
        elif status_filter == 'expired':
            query = query.filter(Notification.expires_at <= datetime.utcnow())
        
        # Get paginated results
        notifications_pagination = query.order_by(
            Notification.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        # Get statistics
        total_notifications = Notification.query.count()
        active_notifications = Notification.query.filter(
            Notification.expires_at > datetime.utcnow()
        ).count()
        expired_notifications = Notification.query.filter(
            Notification.expires_at <= datetime.utcnow()
        ).count()
        
        return render_template('view_notifications.html', 
                           notifications_pagination=notifications_pagination,
                           total_notifications=total_notifications,
                           active_notifications=active_notifications,
                           expired_notifications=expired_notifications,
                           search=search,
                           status_filter=status_filter,
                           user=current_user)
                           
    except Exception as e:
        current_app.logger.error(f"Error loading view notifications: {str(e)}")
        flash('Error loading notifications. Please try again.', 'error')
        return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/notification/<int:notification_id>')
@login_required
@admin_required
def view_notification_detail(notification_id):
    """View individual notification details"""
    try:
        notification = Notification.query.get_or_404(notification_id)
        return render_template('notification_detail.html', 
                           notification=notification,
                           user=current_user)
    except Exception as e:
        current_app.logger.error(f"Error viewing notification detail: {str(e)}")
        flash('Error loading notification details. Please try again.', 'error')
        return redirect(url_for('admin.view_notifications'))


@admin_bp.route('/notifications-stats', methods=['GET'])
@login_required
@admin_required
def notifications_stats():
    """Get real-time notification statistics"""
    try:
        stats = {
            'total_notifications': Notification.query.count(),
            'active_notifications': Notification.query.filter(
                Notification.expires_at > datetime.utcnow()
            ).count(),
            'expired_notifications': Notification.query.filter(
                Notification.expires_at <= datetime.utcnow()
            ).count()
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting notification stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error loading statistics'
        }), 500
'''
    
    # Insert the missing routes before the last function
    admin_content = admin_content.rstrip()
    admin_content += missing_route
    
    with open('app/blueprints/admin.py', 'w', encoding='utf-8') as f:
        f.write(admin_content)
    
    # Fix 2: Update manage_notifications route to be more robust
    old_manage_notifications = '''@admin_bp.route('/notifications')
@login_required
@admin_required
def manage_notifications():
    """Manage notifications"""
    try:
        notifications = Notification.query.order_by(
            Notification.created_at.desc()
        ).all()
        
        return render_template('manage_notifications.html', 
                           notifications=notifications,
                           user=current_user)
    except Exception as e:
        current_app.logger.error(f"Error loading notifications: {str(e)}")
        flash('Error loading notifications. Please try again.', 'error')
        return redirect(url_for('admin.admin_dashboard'))'''
    
    new_manage_notifications = '''@admin_bp.route('/notifications')
@login_required
@admin_required
def manage_notifications():
    """Manage notifications"""
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = 15
        search = request.args.get('search', '')
        status_filter = request.args.get('status', '')
        
        # Build query
        query = Notification.query
        
        # Apply search filter
        if search:
            query = query.filter(
                Notification.title.ilike(f'%{search}%') |
                Notification.content.ilike(f'%{search}%')
            )
        
        # Apply status filter
        if status_filter == 'active':
            query = query.filter(Notification.expires_at > datetime.utcnow())
        elif status_filter == 'expired':
            query = query.filter(Notification.expires_at <= datetime.utcnow())
        
        # Get paginated results
        notifications_pagination = query.order_by(
            Notification.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        # Get statistics
        total_notifications = Notification.query.count()
        active_notifications = Notification.query.filter(
            Notification.expires_at > datetime.utcnow()
        ).count()
        expired_notifications = Notification.query.filter(
            Notification.expires_at <= datetime.utcnow()
        ).count()
        
        return render_template('manage_notifications.html', 
                           notifications_pagination=notifications_pagination,
                           total_notifications=total_notifications,
                           active_notifications=active_notifications,
                           expired_notifications=expired_notifications,
                           search=search,
                           status_filter=status_filter,
                           user=current_user)
                           
    except Exception as e:
        current_app.logger.error(f"Error loading notifications: {str(e)}")
        flash('Error loading notifications. Please try again.', 'error')
        # Return empty data instead of redirecting to avoid infinite loops
        return render_template('manage_notifications.html', 
                           notifications_pagination=None,
                           total_notifications=0,
                           active_notifications=0,
                           expired_notifications=0,
                           search='',
                           status_filter='',
                           user=current_user)'''
    
    admin_content = admin_content.replace(old_manage_notifications, new_manage_notifications)
    
    with open('app/blueprints/admin.py', 'w', encoding='utf-8') as f:
        f.write(admin_content)
    
    # Fix 3: Update manage_notifications.html template to handle pagination
    with open('app/templates/manage_notifications.html', 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Add search and filters
    old_content_start = '''<!-- Notifications List -->
<div class="dashboard-section">
    <div class="section-header">
        <h2 class="section-title"><i class="bi bi-bell"></i> Recent Notifications</h2>
        <a href="{{ url_for('admin.create_notification') }}" class="btn btn-primary">
            <i class="bi bi-plus-lg"></i> Add Notification
        </a>
    </div>'''
    
    new_content_start = '''<!-- Statistics Cards -->
<div class="row mb-4">
    <div class="col-md-3">
        <div class="card bg-primary text-white">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h4 class="mb-0">{{ total_notifications }}</h4>
                        <small>Total Notifications</small>
                    </div>
                    <i class="fas fa-bell fa-2x opacity-75"></i>
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-success text-white">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h4 class="mb-0">{{ active_notifications }}</h4>
                        <small>Active</small>
                    </div>
                    <i class="fas fa-check-circle fa-2x opacity-75"></i>
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-warning text-white">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h4 class="mb-0">{{ expired_notifications }}</h4>
                        <small>Expired</small>
                    </div>
                    <i class="fas fa-clock fa-2x opacity-75"></i>
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-info text-white">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h4 class="mb-0">{{ (active_notifications / total_notifications * 100)|round(1) if total_notifications > 0 else 0 }}%</h4>
                        <small>Active Rate</small>
                    </div>
                    <i class="fas fa-chart-line fa-2x opacity-75"></i>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Search and Filters -->
<div class="card mb-4">
    <div class="card-body">
        <form method="GET" action="{{ url_for('admin.manage_notifications') }}" class="row g-3">
            <div class="col-md-4">
                <label for="search" class="form-label">Search</label>
                <input type="text" class="form-control" id="search" name="search" 
                       value="{{ search }}" placeholder="Search by title or content...">
            </div>
            <div class="col-md-4">
                <label for="status_filter" class="form-label">Status</label>
                <select class="form-select" id="status_filter" name="status_filter">
                    <option value="">All Status</option>
                    <option value="active" {% if status_filter == 'active' %}selected{% endif %}>Active</option>
                    <option value="expired" {% if status_filter == 'expired' %}selected{% endif %}>Expired</option>
                </select>
            </div>
            <div class="col-md-4">
                <label class="form-label">&nbsp;</label>
                <div class="d-flex gap-2">
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-search me-2"></i> Search
                    </button>
                    <a href="{{ url_for('admin.manage_notifications') }}" class="btn btn-outline-secondary">
                        <i class="fas fa-times me-2"></i> Clear
                    </a>
                    <a href="{{ url_for('admin.create_notification') }}" class="btn btn-success">
                        <i class="bi bi-plus-lg"></i> Add New
                    </a>
                </div>
            </div>
        </form>
    </div>
</div>

<!-- Notifications List -->
<div class="dashboard-section">
    <div class="section-header">
        <h2 class="section-title"><i class="bi bi-bell"></i> Notifications List</h2>
        <div class="d-flex gap-2">
            <button class="btn btn-outline-primary btn-sm" onclick="refreshNotifications()">
                <i class="fas fa-sync-alt"></i> Refresh
            </button>
        </div>
    </div>'''
    
    template_content = template_content.replace(old_content_start, new_content_start)
    
    # Update the notifications table to handle pagination
    old_table = '''    {% if notifications %}
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>Title</th>
                        <th>Type</th>
                        <th>Priority</th>
                        <th>Created</th>
                        <th>Expires</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for notification in notifications %}
                    <tr>
                        <td>
                            <strong>{{ notification.title }}</strong>
                            {% if notification.link_url %}
                            <br><small><a href="{{ notification.link_url }}" target="_blank">View Link</a></small>
                            {% endif %}
                        </td>
                        <td>
                            <span class="badge bg-{{ 'primary' if notification.notification_type == 'general' else 'info' if notification.notification_type == 'academic' else 'warning' }}">
                                {{ notification.notification_type.title() }}
                            </span>
                        </td>
                        <td>
                            <span class="badge bg-{{ 'danger' if notification.priority == 'high' else 'warning' if notification.priority == 'medium' else 'info' }}">
                                {{ notification.priority.title() }}
                            </span>
                        </td>
                        <td>{{ notification.created_at.strftime('%b %d, %Y %I:%M %p') if notification.created_at else 'N/A' }}</td>
                        <td>{{ notification.expires_at.strftime('%b %d, %Y %I:%M %p') if notification.expires_at else 'Never' }}</td>
                        <td>
                            {% from datetime import datetime %}
                            {% set now = datetime.utcnow() %}
                            {% if notification.expires_at and notification.expires_at < now %}
                            <span class="badge bg-secondary">Expired</span>
                            {% else %}
                            <span class="badge bg-success">Active</span>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    {% else %}
        <div class="text-center py-5">
            <i class="bi bi-bell-slash fa-3x text-muted mb-3"></i>
            <h5 class="text-muted">No Notifications Found</h5>
            <p class="text-muted">No notifications have been created yet.</p>
            <a href="{{ url_for('admin.create_notification') }}" class="btn btn-primary">
                <i class="bi bi-plus-lg"></i> Create First Notification
            </a>
        </div>
    {% endif %}'''
    
    new_table = '''    {% if notifications_pagination and notifications_pagination.items %}
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>Title</th>
                        <th>Type</th>
                        <th>Priority</th>
                        <th>Created</th>
                        <th>Expires</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for notification in notifications_pagination.items %}
                    <tr>
                        <td>
                            <strong>{{ notification.title }}</strong>
                            {% if notification.link_url %}
                            <br><small><a href="{{ notification.link_url }}" target="_blank">View Link</a></small>
                            {% endif %}
                            {% if notification.content %}
                            <br><small class="text-muted">{{ notification.content[:100] }}{% if notification.content|length > 100 %}...{% endif %}</small>
                            {% endif %}
                        </td>
                        <td>
                            <span class="badge bg-{{ 'primary' if notification.notification_type == 'general' else 'info' if notification.notification_type == 'academic' else 'warning' }}">
                                {{ notification.notification_type.title() }}
                            </span>
                        </td>
                        <td>
                            <span class="badge bg-{{ 'danger' if notification.priority == 'high' else 'warning' if notification.priority == 'medium' else 'info' }}">
                                {{ notification.priority.title() }}
                            </span>
                        </td>
                        <td>{{ notification.created_at.strftime('%b %d, %Y %I:%M %p') if notification.created_at else 'N/A' }}</td>
                        <td>{{ notification.expires_at.strftime('%b %d, %Y %I:%M %p') if notification.expires_at else 'Never' }}</td>
                        <td>
                            {% from datetime import datetime %}
                            {% set now = datetime.utcnow() %}
                            {% if notification.expires_at and notification.expires_at < now %}
                            <span class="badge bg-secondary">Expired</span>
                            {% else %}
                            <span class="badge bg-success">Active</span>
                            {% endif %}
                        </td>
                        <td>
                            <div class="btn-group btn-group-sm">
                                <a href="{{ url_for('admin.view_notification_detail', notification_id=notification.id) }}" class="btn btn-outline-primary" title="View Details">
                                    <i class="fas fa-eye"></i>
                                </a>
                                <a href="{{ url_for('notification.edit_notification', notification_id=notification.id) }}" class="btn btn-outline-warning" title="Edit">
                                    <i class="fas fa-edit"></i>
                                </a>
                                <form method="POST" action="{{ url_for('admin.delete_notification', notification_id=notification.id) }}" style="display: inline;">
                                    <button type="submit" class="btn btn-outline-danger" title="Delete" onclick="return confirm('Are you sure you want to delete this notification?')">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </form>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <!-- Pagination -->
        {% if notifications_pagination.pages > 1 %}
        <nav aria-label="Notifications pagination">
            <ul class="pagination justify-content-center">
                {% if notifications_pagination.has_prev %}
                <li class="page-item">
                    <a class="page-link" href="{{ url_for('admin.manage_notifications', page=notifications_pagination.prev_num, search=search, status_filter=status_filter) }}">Previous</a>
                </li>
                {% endif %}
                
                {% for page_num in notifications_pagination.iter_pages() %}
                    {% if page_num %}
                        {% if page_num != notifications_pagination.page %}
                        <li class="page-item">
                            <a class="page-link" href="{{ url_for('admin.manage_notifications', page=page_num, search=search, status_filter=status_filter) }}">{{ page_num }}</a>
                        </li>
                        {% else %}
                        <li class="page-item active">
                            <span class="page-link">{{ page_num }}</span>
                        </li>
                        {% endif %}
                    {% else %}
                    <li class="page-item disabled">
                        <span class="page-link">...</span>
                    </li>
                    {% endif %}
                {% endfor %}
                
                {% if notifications_pagination.has_next %}
                <li class="page-item">
                    <a class="page-link" href="{{ url_for('admin.manage_notifications', page=notifications_pagination.next_num, search=search, status_filter=status_filter) }}">Next</a>
                </li>
                {% endif %}
            </ul>
        </nav>
        {% endif %}
    {% else %}
        <div class="text-center py-5">
            <i class="bi bi-bell-slash fa-3x text-muted mb-3"></i>
            <h5 class="text-muted">No Notifications Found</h5>
            <p class="text-muted">
                {% if search or status_filter %}
                    Try adjusting your search or filters to see more results.
                {% else %}
                    No notifications have been created yet.
                {% endif %}
            </p>
            {% if search or status_filter %}
                <a href="{{ url_for('admin.manage_notifications') }}" class="btn btn-outline-primary me-2">
                    <i class="fas fa-times me-2"></i> Clear Filters
                </a>
            {% endif %}
            <a href="{{ url_for('admin.create_notification') }}" class="btn btn-primary">
                <i class="bi bi-plus-lg"></i> Create First Notification
            </a>
        </div>
    {% endif %}'''
    
    template_content = template_content.replace(old_table, new_table)
    
    # Add JavaScript for real-time updates
    template_content += '''

<script>
// Real-time notification updates
function refreshNotifications() {
    fetch('/admin/notifications-stats')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update statistics cards
                updateNotificationStats(data.stats);
            }
        })
        .catch(error => console.log('Error refreshing notifications:', error));
    
    // Reload the page after a short delay to show updated data
    setTimeout(() => {
        window.location.reload();
    }, 500);
}

function updateNotificationStats(stats) {
    // Update statistics cards with animation
    const cards = {
        'total_notifications': stats.total_notifications,
        'active_notifications': stats.active_notifications,
        'expired_notifications': stats.expired_notifications
    };
    
    Object.keys(cards).forEach((key, index) => {
        const cardElement = document.querySelectorAll('.card-body h4')[index];
        if (cardElement && cards[key] !== undefined) {
            animateValue(cardElement, parseInt(cardElement.textContent), cards[key], 1000);
        }
    });
}

function animateValue(element, start, end, duration) {
    const startTime = performance.now();
    const animate = (currentTime) => {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const current = Math.floor(start + (end - start) * progress);
        element.textContent = current;
        
        if (progress < 1) {
            requestAnimationFrame(animate);
        }
    };
    requestAnimationFrame(animate);
}

// Auto-refresh notifications every 60 seconds
setInterval(() => {
    refreshNotifications();
}, 60000);

// Initialize tooltips
document.addEventListener('DOMContentLoaded', () => {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
</script>'''
    
    with open('app/templates/manage_notifications.html', 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    print("Fixed notification view feature!")
    print("\nChanges made:")
    print("1. Added missing view_notifications route")
    print("2. Enhanced manage_notifications route with pagination and search")
    print("3. Added notification statistics and filtering")
    print("4. Updated template with pagination and search functionality")
    print("5. Added real-time updates and auto-refresh")
    print("6. Added notification detail view and action buttons")
    print("\nThe notification view feature should now load properly!")

if __name__ == "__main__":
    fix_notification_view()
