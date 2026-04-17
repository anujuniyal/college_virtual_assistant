#!/usr/bin/env python3
"""
Add real-time data functionality to FAQ feature in admin dashboard
"""

def fix_faq_realtime():
    """Add real-time updates to FAQ management"""
    
    # Fix 1: Update manage_faqs route to include pagination, search, and filtering
    with open('app/blueprints/admin.py', 'r', encoding='utf-8') as f:
        admin_content = f.read()
    
    old_manage_faqs = '''@admin_bp.route('/faqs')
@login_required
@admin_required
def manage_faqs():
    """Manage frequently asked questions"""
    try:
        faqs = FAQ.query.order_by(
            FAQ.priority.desc(), FAQ.created_at.desc()
        ).all()
        
        return render_template('manage_faqs.html', 
                           faqs=faqs,
                           user=current_user)
    except Exception as e:
        current_app.logger.error(f"Error loading FAQs: {str(e)}")
        flash('Error loading FAQs. Please try again.', 'error')
        return redirect(url_for('admin.admin_dashboard'))'''
    
    new_manage_faqs = '''@admin_bp.route('/faqs')
@login_required
@admin_required
def manage_faqs():
    """Manage frequently asked questions"""
    try:
        # Get pagination and filter parameters
        page = request.args.get('page', 1, type=int)
        per_page = 10
        search = request.args.get('search', '')
        selected_category = request.args.get('category', '')
        selected_priority = request.args.get('priority', '')
        
        # Build query
        query = FAQ.query
        
        # Apply search filter
        if search:
            query = query.filter(
                FAQ.question.ilike(f'%{search}%') |
                FAQ.answer.ilike(f'%{search}%')
            )
        
        # Apply category filter
        if selected_category:
            query = query.filter(FAQ.category == selected_category)
        
        # Apply priority filter
        if selected_priority:
            query = query.filter(FAQ.priority == int(selected_priority))
        
        # Get paginated results
        faq_pagination = query.order_by(
            FAQ.priority.desc(), FAQ.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        # Get statistics
        total_faqs = FAQ.query.count()
        active_faqs = FAQ.query.filter_by(is_active=True).count()
        total_views = db.session.query(db.func.sum(FAQ.view_count)).scalar() or 0
        
        return render_template('manage_faqs.html', 
                           faq_pagination=faq_pagination,
                           total_faqs=total_faqs,
                           active_faqs=active_faqs,
                           total_views=total_views,
                           search=search,
                           selected_category=selected_category,
                           selected_priority=selected_priority,
                           user=current_user)
                           
    except Exception as e:
        current_app.logger.error(f"Error loading FAQs: {str(e)}")
        flash('Error loading FAQs. Please try again.', 'error')
        # Return empty data instead of redirecting to avoid infinite loops
        return render_template('manage_faqs.html', 
                           faq_pagination=None,
                           total_faqs=0,
                           active_faqs=0,
                           total_views=0,
                           search='',
                           selected_category='',
                           selected_priority='',
                           user=current_user)'''
    
    admin_content = admin_content.replace(old_manage_faqs, new_manage_faqs)
    
    # Add FAQ real-time endpoints
    faq_endpoints = '''

@admin_bp.route('/faqs-stats', methods=['GET'])
@login_required
@admin_required
def faqs_stats():
    """Get real-time FAQ statistics"""
    try:
        stats = {
            'total_faqs': FAQ.query.count(),
            'active_faqs': FAQ.query.filter_by(is_active=True).count(),
            'inactive_faqs': FAQ.query.filter_by(is_active=False).count(),
            'total_views': db.session.query(db.func.sum(FAQ.view_count)).scalar() or 0,
            'high_priority': FAQ.query.filter_by(priority=3).count(),
            'medium_priority': FAQ.query.filter_by(priority=2).count(),
            'low_priority': FAQ.query.filter_by(priority=1).count()
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting FAQ stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error loading statistics'
        }), 500


@admin_bp.route('/refresh-faqs', methods=['POST'])
@login_required
@admin_required
def refresh_faqs():
    """Refresh FAQ data with real-time updates"""
    try:
        # Get current parameters
        page = request.json.get('page', 1)
        search = request.json.get('search', '')
        selected_category = request.json.get('category', '')
        selected_priority = request.json.get('priority', '')
        
        # Build query
        query = FAQ.query
        
        # Apply filters
        if search:
            query = query.filter(
                FAQ.question.ilike(f'%{search}%') |
                FAQ.answer.ilike(f'%{search}%')
            )
        
        if selected_category:
            query = query.filter(FAQ.category == selected_category)
        
        if selected_priority:
            query = query.filter(FAQ.priority == int(selected_priority))
        
        # Get paginated results
        faq_pagination = query.order_by(
            FAQ.priority.desc(), FAQ.created_at.desc()
        ).paginate(page=page, per_page=10, error_out=False)
        
        # Format FAQ data for JSON response
        faqs_data = []
        for faq in faq_pagination.items:
            faqs_data.append({
                'id': faq.id,
                'question': faq.question,
                'answer': faq.answer,
                'category': faq.category,
                'priority': faq.priority,
                'view_count': faq.view_count,
                'is_active': faq.is_active,
                'updated_at': faq.updated_at.strftime('%d %b %Y') if faq.updated_at else '',
                'priority_label': 'High' if faq.priority == 3 else 'Medium' if faq.priority == 2 else 'Low'
            })
        
        return jsonify({
            'success': True,
            'faqs': faqs_data,
            'pagination': {
                'page': faq_pagination.page,
                'pages': faq_pagination.pages,
                'total': faq_pagination.total,
                'has_prev': faq_pagination.has_prev,
                'has_next': faq_pagination.has_next
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error refreshing FAQs: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error refreshing FAQ data'
        }), 500


@admin_bp.route('/toggle-faq-status/<int:faq_id>', methods=['POST'])
@login_required
@admin_required
def toggle_faq_status(faq_id):
    """Toggle FAQ active/inactive status"""
    try:
        faq = FAQ.query.get_or_404(faq_id)
        faq.is_active = not faq.is_active
        faq.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'FAQ {"activated" if faq.is_active else "deactivated"} successfully',
            'is_active': faq.is_active
        })
        
    except Exception as e:
        current_app.logger.error(f"Error toggling FAQ status: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error updating FAQ status'
        }), 500
'''
    
    admin_content += faq_endpoints
    
    with open('app/blueprints/admin.py', 'w', encoding='utf-8') as f:
        f.write(admin_content)
    
    # Fix 2: Update manage_faqs.html template to include statistics and real-time features
    with open('app/templates/manage_faqs.html', 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Add statistics cards
    old_header = '''            <div class="d-flex justify-content-between align-items-center mb-4">
                <div class="d-flex align-items-center gap-2">
                    <h2 class="h4 mb-0">Manage FAQs</h2>
                    <span class="badge bg-warning">Frequently Asked Questions</span>
                </div>
                <div class="d-flex gap-2">
                    <a href="{{ url_for('admin.admin_dashboard') }}" class="btn btn-outline-info">
                        <i class="fas fa-tachometer-alt me-2"></i> Dashboard
                    </a>
                    <a href="{{ url_for('admin.manage_complaints') }}" class="btn btn-outline-warning">
                        <i class="fas fa-list-alt me-2"></i> FAQ Records
                    </a>
                    <a href="{{ url_for('admin.add_faq') }}" class="btn btn-success">
                        <i class="fas fa-plus me-2"></i> Add FAQ
                    </a>
                </div>
            </div>'''
    
    new_header = '''            <div class="d-flex justify-content-between align-items-center mb-4">
                <div class="d-flex align-items-center gap-2">
                    <h2 class="h4 mb-0">Manage FAQs</h2>
                    <span class="badge bg-warning">Frequently Asked Questions</span>
                </div>
                <div class="d-flex gap-2">
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
                </div>
            </div>

            <!-- Statistics Cards -->
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="card bg-primary text-white">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <h4 class="mb-0" data-faq-stat="total">{{ total_faqs }}</h4>
                                    <small>Total FAQs</small>
                                </div>
                                <i class="fas fa-question-circle fa-2x opacity-75"></i>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-success text-white">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <h4 class="mb-0" data-faq-stat="active">{{ active_faqs }}</h4>
                                    <small>Active</small>
                                </div>
                                <i class="fas fa-check-circle fa-2x opacity-75"></i>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-info text-white">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <h4 class="mb-0" data-faq-stat="views">{{ total_views }}</h4>
                                    <small>Total Views</small>
                                </div>
                                <i class="fas fa-eye fa-2x opacity-75"></i>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-warning text-white">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <h4 class="mb-0" data-faq-stat="active-rate">{{ ((active_faqs / total_faqs * 100)|round(1) if total_faqs > 0 else 0) }}%</h4>
                                    <small>Active Rate</small>
                                </div>
                                <i class="fas fa-chart-line fa-2x opacity-75"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>'''
    
    template_content = template_content.replace(old_header, new_header)
    
    # Update the filters to be functional
    old_filters = '''            <!-- Filters -->
            <div class="card mb-4">
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-3">
                            <div class="input-group">
                                <i class="bi bi-search" style="font-size: 14px;"></i>
                                <input type="text" class="form-control" name="search" 
                                       value="{{ search }}" placeholder="Search FAQs...">
                            </div>
                        </div>
                        <div class="col-md-3">
                            <i class="bi bi-tag" style="font-size: 14px;"></i>
                            <select class="form-control" name="category">
                                <option value="">All Categories</option>
                                <option value="general">General</option>
                                <option value="admission">Admission</option>
                                <option value="course">Course</option>
                                <option value="fee">Fee</option>
                                <option value="facility">Facilities</option>
                                <option value="faculty">Faculty</option>
                                <option value="complaint">Complaint Process</option>
                                <option value="other">Other</option>
                            </select>
                        </div>
                        <div class="col-md-2">
                            <select class="form-control" name="priority">
                                <option value="">All Priorities</option>
                                <option value="1" {% if selected_priority == '1' %}selected{% endif %}>Low Priority</option>
                                <option value="2" {% if selected_priority == '2' %}selected{% endif %}>Medium Priority</option>
                                <option value="3" {% if selected_priority == '3' %}selected{% endif %}>High Priority</option>
                            </select>
                        </div>
                        <div class="col-md-2">
                            <button type="submit" class="btn btn-primary w-100">
                                <i class="bi bi-funnel"></i>Filter
                            </button>
                            <a href="{{ url_for('admin.manage_faqs') }}" class="btn btn-outline-secondary w-100">
                                <i class="bi bi-arrow-clockwise"></i>Clear
                            </a>
                        </div>
                    </div>
                </div>
            </div>'''
    
    new_filters = '''            <!-- Filters -->
            <div class="card mb-4">
                <div class="card-body">
                    <form method="GET" action="{{ url_for('admin.manage_faqs') }}" class="row g-3">
                        <div class="col-md-3">
                            <label for="search" class="form-label">Search</label>
                            <div class="input-group">
                                <i class="bi bi-search" style="font-size: 14px;"></i>
                                <input type="text" class="form-control" id="search" name="search" 
                                       value="{{ search }}" placeholder="Search FAQs...">
                            </div>
                        </div>
                        <div class="col-md-3">
                            <label for="category" class="form-label">Category</label>
                            <i class="bi bi-tag" style="font-size: 14px;"></i>
                            <select class="form-control" id="category" name="category">
                                <option value="">All Categories</option>
                                <option value="general" {% if selected_category == 'general' %}selected{% endif %}>General</option>
                                <option value="admission" {% if selected_category == 'admission' %}selected{% endif %}>Admission</option>
                                <option value="course" {% if selected_category == 'course' %}selected{% endif %}>Course</option>
                                <option value="fee" {% if selected_category == 'fee' %}selected{% endif %}>Fee</option>
                                <option value="facility" {% if selected_category == 'facility' %}selected{% endif %}>Facilities</option>
                                <option value="faculty" {% if selected_category == 'faculty' %}selected{% endif %}>Faculty</option>
                                <option value="complaint" {% if selected_category == 'complaint' %}selected{% endif %}>Complaint Process</option>
                                <option value="other" {% if selected_category == 'other' %}selected{% endif %}>Other</option>
                            </select>
                        </div>
                        <div class="col-md-2">
                            <label for="priority" class="form-label">Priority</label>
                            <select class="form-control" id="priority" name="priority">
                                <option value="">All Priorities</option>
                                <option value="1" {% if selected_priority == '1' %}selected{% endif %}>Low Priority</option>
                                <option value="2" {% if selected_priority == '2' %}selected{% endif %}>Medium Priority</option>
                                <option value="3" {% if selected_priority == '3' %}selected{% endif %}>High Priority</option>
                            </select>
                        </div>
                        <div class="col-md-2">
                            <label class="form-label">&nbsp;</label>
                            <div class="d-flex gap-2">
                                <button type="submit" class="btn btn-primary w-100">
                                    <i class="bi bi-funnel"></i>Filter
                                </button>
                                <a href="{{ url_for('admin.manage_faqs') }}" class="btn btn-outline-secondary w-100">
                                    <i class="bi bi-arrow-clockwise"></i>Clear
                                </a>
                            </div>
                        </div>
                    </form>
                </div>
            </div>'''
    
    template_content = template_content.replace(old_filters, new_filters)
    
    # Add status toggle functionality to actions
    old_actions = '''                                        <td>
                                            <div class="btn-group btn-group-sm" role="group">
                                                <a href="{{ url_for('admin.edit_faq', faq_id=faq.id) }}" 
                                                   class="btn btn-outline-primary" title="Edit">
                                                    <i class="bi bi-pencil"></i>
                                                </a>
                                                <form method="POST" action="{{ url_for('admin.delete_faq', faq_id=faq.id) }}" 
                                                      class="d-inline" onsubmit="return confirm('Are you sure you want to delete this FAQ?')">
                                                    <button type="submit" class="btn btn-outline-danger" title="Delete">
                                                        <i class="bi bi-trash"></i>
                                                    </button>
                                                </form>
                                            </div>
                                        </td>'''
    
    new_actions = '''                                        <td>
                                            <div class="btn-group btn-group-sm" role="group">
                                                <a href="{{ url_for('admin.edit_faq', faq_id=faq.id) }}" 
                                                   class="btn btn-outline-primary" title="Edit">
                                                    <i class="bi bi-pencil"></i>
                                                </a>
                                                <button class="btn btn-outline-{{ 'success' if faq.is_active else 'secondary' }}" 
                                                        onclick="toggleFAQStatus({{ faq.id }})" 
                                                        title="{{ 'Deactivate' if faq.is_active else 'Activate' }}">
                                                    <i class="fas fa-{{ 'pause' if faq.is_active else 'play' }}"></i>
                                                </button>
                                                <form method="POST" action="{{ url_for('admin.delete_faq', faq_id=faq.id) }}" 
                                                      class="d-inline" onsubmit="return confirm('Are you sure you want to delete this FAQ?')">
                                                    <button type="submit" class="btn btn-outline-danger" title="Delete">
                                                        <i class="bi bi-trash"></i>
                                                    </button>
                                                </form>
                                            </div>
                                        </td>'''
    
    template_content = template_content.replace(old_actions, new_actions)
    
    # Add JavaScript for real-time updates
    template_content += '''

<script>
// Real-time FAQ management
let currentPage = 1;
let currentFilters = {
    search: '',
    category: '',
    priority: ''
};

// Initialize FAQ page
document.addEventListener('DOMContentLoaded', () => {
    // Get current filters from URL
    const urlParams = new URLSearchParams(window.location.search);
    currentFilters.search = urlParams.get('search') || '';
    currentFilters.category = urlParams.get('category') || '';
    currentFilters.priority = urlParams.get('priority') || '';
    currentPage = parseInt(urlParams.get('page')) || 1;
    
    // Start auto-refresh
    startFAQAutoRefresh();
});

function refreshFAQs() {
    // Show loading state
    const refreshBtn = document.querySelector('button[onclick="refreshFAQs()"]');
    if (refreshBtn) {
        refreshBtn.disabled = true;
        refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
    }
    
    // Fetch fresh data
    fetch('/admin/faqs-stats')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateFAQStats(data.stats);
            }
        })
        .catch(error => console.log('Error refreshing FAQ stats:', error))
        .finally(() => {
            // Reset button
            if (refreshBtn) {
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
            }
        });
    
    // Reload page after short delay to show updated data
    setTimeout(() => {
        window.location.reload();
    }, 500);
}

function updateFAQStats(stats) {
    // Update statistics cards with animation
    const updates = {
        'total': stats.total_faqs,
        'active': stats.active_faqs,
        'views': stats.total_views,
        'active-rate': stats.total_faqs > 0 ? ((stats.active_faqs / stats.total_faqs * 100).toFixed(1)) : 0
    };
    
    Object.keys(updates).forEach((key, index) => {
        const element = document.querySelector(`[data-faq-stat="${key}"]`);
        if (element && updates[key] !== undefined) {
            animateValue(element, parseInt(element.textContent) || 0, updates[key], 1000);
        }
    });
}

function toggleFAQStatus(faqId) {
    fetch(`/admin/toggle-faq-status/${faqId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message
            showNotification(data.message, 'success');
            // Refresh the page to show updated status
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showNotification(data.message, 'error');
        }
    })
    .catch(error => {
        console.log('Error toggling FAQ status:', error);
        showNotification('Error updating FAQ status', 'error');
    });
}

function startFAQAutoRefresh() {
    // Auto-refresh FAQ statistics every 60 seconds
    setInterval(() => {
        fetch('/admin/faqs-stats')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateFAQStats(data.stats);
                }
            })
            .catch(error => console.log('Auto-refresh error:', error));
    }, 60000);
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

function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container-fluid');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

// Initialize tooltips
document.addEventListener('DOMContentLoaded', () => {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
</script>'''
    
    with open('app/templates/manage_faqs.html', 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    print("Added real-time functionality to FAQ feature!")
    print("\nChanges made:")
    print("1. Enhanced manage_faqs route with pagination and filtering")
    print("2. Added real-time FAQ statistics endpoint")
    print("3. Added FAQ refresh endpoint for AJAX updates")
    print("4. Added FAQ status toggle functionality")
    print("5. Updated template with statistics cards and filters")
    print("6. Added JavaScript for real-time updates and auto-refresh")
    print("7. Added animated counters and notifications")
    print("\nThe FAQ feature now works with real-time data!")

if __name__ == "__main__":
    fix_faq_realtime()
