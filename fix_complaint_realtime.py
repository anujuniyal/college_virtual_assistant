#!/usr/bin/env python3
"""
Fix complaint feature real-time data fetching in admin dashboard
"""

def fix_complaint_realtime():
    """Add real-time complaint data fetching to admin dashboard"""
    
    # Fix 1: Update admin dashboard route to include complaint statistics
    with open('app/blueprints/admin.py', 'r', encoding='utf-8') as f:
        admin_content = f.read()
    
    old_dashboard_query = '''        # Get dashboard metrics
        total_students = Student.query.count() if Student else 0
        total_faculty = Faculty.query.count() if Faculty else 0
        active_notifications = Notification.query.count() if Notification else 0
        pending_complaints = Complaint.query.filter_by(status='pending').count() if Complaint else 0'''
    
    new_dashboard_query = '''        # Get dashboard metrics
        total_students = Student.query.count() if Student else 0
        total_faculty = Faculty.query.count() if Faculty else 0
        active_notifications = Notification.query.count() if Notification else 0
        
        # Get complaint statistics
        if Complaint:
            total_complaints = Complaint.query.count()
            pending_complaints = Complaint.query.filter_by(status='pending').count()
            investigating_complaints = Complaint.query.filter_by(status='investigating').count()
            resolved_complaints = Complaint.query.filter_by(status='resolved').count()
        else:
            total_complaints = pending_complaints = investigating_complaints = resolved_complaints = 0'''
    
    old_dashboard_return = '''        return render_template('admin_dashboard_edubot.html', 
                           total_students=total_students,
                           total_faculty=total_faculty,
                           total_notifications=active_notifications,
                           user=current_user)'''
    
    new_dashboard_return = '''        return render_template('admin_dashboard_edubot.html', 
                           total_students=total_students,
                           total_faculty=total_faculty,
                           total_notifications=active_notifications,
                           total_complaints=total_complaints,
                           pending_complaints=pending_complaints,
                           investigating_complaints=investigating_complaints,
                           resolved_complaints=resolved_complaints,
                           user=current_user)'''
    
    old_error_return = '''        return render_template('admin_dashboard_edubot.html', 
                           total_students=0,
                           total_faculty=0,
                           total_notifications=0,
                           user=current_user)'''
    
    new_error_return = '''        return render_template('admin_dashboard_edubot.html', 
                           total_students=0,
                           total_faculty=0,
                           total_notifications=0,
                           total_complaints=0,
                           pending_complaints=0,
                           investigating_complaints=0,
                           resolved_complaints=0,
                           user=current_user)'''
    
    admin_content = admin_content.replace(old_dashboard_query, new_dashboard_query)
    admin_content = admin_content.replace(old_dashboard_return, new_dashboard_return)
    admin_content = admin_content.replace(old_error_return, new_error_return)
    
    # Fix 2: Update refresh_activity endpoint to include complaints
    old_refresh_activity = '''        # Get recent student registrations if any
        recent_students = Student.query.order_by(
            Student.created_at.desc()
        ).limit(3).all() if Student else []
        
        for student in recent_students:
            activities.append({
                'text': f"New student registered: {student.name}",
                'time': format_time_ago(student.created_at),
                'icon': 'user-graduate',
                'color': 'success'
            })
        
        return jsonify({
            'success': True,
            'activities': activities[:10]  # Limit to 10 most recent
        })'''
    
    new_refresh_activity = '''        # Get recent student registrations if any
        recent_students = Student.query.order_by(
            Student.created_at.desc()
        ).limit(3).all() if Student else []
        
        for student in recent_students:
            activities.append({
                'text': f"New student registered: {student.name}",
                'time': format_time_ago(student.created_at),
                'icon': 'user-graduate',
                'color': 'success'
            })
        
        # Get recent complaints
        recent_complaints = Complaint.query.order_by(
            Complaint.created_at.desc()
        ).limit(3).all() if Complaint else []
        
        for complaint in recent_complaints:
            activities.append({
                'text': f"New complaint filed: {complaint.category.title()} - {complaint.description[:50]}...",
                'time': format_time_ago(complaint.created_at),
                'icon': 'exclamation-triangle',
                'color': 'warning'
            })
        
        return jsonify({
            'success': True,
            'activities': activities[:10],  # Limit to 10 most recent
            'total_complaints': Complaint.query.count() if Complaint else 0,
            'pending_complaints': Complaint.query.filter_by(status='pending').count() if Complaint else 0,
            'investigating_complaints': Complaint.query.filter_by(status='investigating').count() if Complaint else 0,
            'resolved_complaints': Complaint.query.filter_by(status='resolved').count() if Complaint else 0
        })'''
    
    admin_content = admin_content.replace(old_refresh_activity, new_refresh_activity)
    
    # Fix 3: Fix manage_complaints route to include statistics and pagination
    old_manage_complaints = '''@admin_bp.route('/complaints')
@login_required
@admin_required
def manage_complaints():
    """Manage complaints"""
    try:
        complaints = Complaint.query.order_by(
            Complaint.created_at.desc()
        ).all()
        
        return render_template('manage_complaints.html', 
                           complaints=complaints,
                           user=current_user)
    except Exception as e:
        current_app.logger.error(f"Error loading complaints: {str(e)}")
        flash('Error loading complaints. Please try again.', 'error')
        return redirect(url_for('admin.admin_dashboard'))'''
    
    new_manage_complaints = '''@admin_bp.route('/complaints')
@login_required
@admin_required
def manage_complaints():
    """Manage complaints"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        selected_status = request.args.get('status', '')
        selected_category = request.args.get('category', '')
        
        # Build query with filters
        query = Complaint.query
        
        if selected_status:
            query = query.filter(Complaint.status == selected_status)
        
        if selected_category:
            query = query.filter(Complaint.category == selected_category)
        
        # Get paginated results
        complaints_pagination = query.order_by(
            Complaint.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        # Get statistics
        total_complaints = Complaint.query.count()
        pending_complaints = Complaint.query.filter_by(status='pending').count()
        investigating_complaints = Complaint.query.filter_by(status='investigating').count()
        resolved_complaints = Complaint.query.filter_by(status='resolved').count()
        
        return render_template('manage_complaints.html', 
                           complaints_pagination=complaints_pagination,
                           total_complaints=total_complaints,
                           pending_complaints=pending_complaints,
                           investigating_complaints=investigating_complaints,
                           resolved_complaints=resolved_complaints,
                           selected_status=selected_status,
                           selected_category=selected_category,
                           user=current_user)
    except Exception as e:
        current_app.logger.error(f"Error loading complaints: {str(e)}")
        flash('Error loading complaints. Please try again.', 'error')
        return redirect(url_for('admin.admin_dashboard'))'''
    
    admin_content = admin_content.replace(old_manage_complaints, new_manage_complaints)
    
    with open('app/blueprints/admin.py', 'w', encoding='utf-8') as f:
        f.write(admin_content)
    
    # Fix 4: Add missing view_complaint and delete_complaint routes
    missing_routes = '''

@admin_bp.route('/view-complaint/<int:complaint_id>')
@login_required
@admin_required
def view_complaint(complaint_id):
    """View complaint details"""
    try:
        complaint = Complaint.query.get_or_404(complaint_id)
        return render_template('view_complaint.html', 
                           complaint=complaint,
                           user=current_user)
    except Exception as e:
        current_app.logger.error(f"Error viewing complaint: {str(e)}")
        flash('Error loading complaint details. Please try again.', 'error')
        return redirect(url_for('admin.manage_complaints'))


@admin_bp.route('/delete-complaint/<int:complaint_id>', methods=['POST'])
@login_required
@admin_required
def delete_complaint(complaint_id):
    """Delete complaint"""
    try:
        complaint = Complaint.query.get_or_404(complaint_id)
        db.session.delete(complaint)
        db.session.commit()
        
        flash('Complaint deleted successfully.', 'success')
        return redirect(url_for('admin.manage_complaints'))
        
    except Exception as e:
        current_app.logger.error(f"Error deleting complaint: {str(e)}")
        flash('Error deleting complaint. Please try again.', 'error')
        return redirect(url_for('admin.manage_complaints'))


@admin_bp.route('/update-complaint-status/<int:complaint_id>', methods=['POST'])
@login_required
@admin_required
def update_complaint_status(complaint_id):
    """Update complaint status"""
    try:
        complaint = Complaint.query.get_or_404(complaint_id)
        new_status = request.json.get('status')
        
        if new_status in ['pending', 'investigating', 'resolved']:
            complaint.status = new_status
            if new_status == 'resolved':
                complaint.resolved_at = datetime.utcnow()
                complaint.resolved_by = current_user.id
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Complaint status updated to {new_status}'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid status'
            })
        
    except Exception as e:
        current_app.logger.error(f"Error updating complaint status: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error updating complaint status'
        }), 500


@admin_bp.route('/complaints-stats', methods=['GET'])
@login_required
@admin_required
def complaints_stats():
    """Get real-time complaint statistics"""
    try:
        stats = {
            'total_complaints': Complaint.query.count() if Complaint else 0,
            'pending_complaints': Complaint.query.filter_by(status='pending').count() if Complaint else 0,
            'investigating_complaints': Complaint.query.filter_by(status='investigating').count() if Complaint else 0,
            'resolved_complaints': Complaint.query.filter_by(status='resolved').count() if Complaint else 0
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting complaint stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error loading statistics'
        }), 500
'''
    
    admin_content += missing_routes
    
    with open('app/blueprints/admin.py', 'w', encoding='utf-8') as f:
        f.write(admin_content)
    
    # Fix 5: Update dashboard JavaScript to handle complaint data
    with open('app/static/js/dashboard.js', 'r', encoding='utf-8') as f:
        js_content = f.read()
    
    old_update_summary = '''    updateSummaryCards(data) {
        const cards = document.querySelectorAll('.card-count');
        const keys = ['total_students', 'total_faculty', 'total_notifications', 'pending_complaints'];
        
        keys.forEach((key, index) => {
            if (cards[index] && data[key] !== undefined) {
                this.animateNumber(cards[index], data[key]);
            }
        });
    }'''
    
    new_update_summary = '''    updateSummaryCards(data) {
        const cards = document.querySelectorAll('.card-count');
        const keys = ['total_students', 'total_faculty', 'total_notifications', 'total_complaints'];
        
        keys.forEach((key, index) => {
            if (cards[index] && data[key] !== undefined) {
                this.animateNumber(cards[index], data[key]);
            }
        });
        
        // Update complaint-specific cards if they exist
        this.updateComplaintCards(data);
    }
    
    updateComplaintCards(data) {
        // Update pending complaints card
        const pendingCard = document.querySelector('[data-complaint-stat="pending"]');
        if (pendingCard && data.pending_complaints !== undefined) {
            this.animateNumber(pendingCard, data.pending_complaints);
        }
        
        // Update investigating complaints card
        const investigatingCard = document.querySelector('[data-complaint-stat="investigating"]');
        if (investigatingCard && data.investigating_complaints !== undefined) {
            this.animateNumber(investigatingCard, data.investigating_complaints);
        }
        
        // Update resolved complaints card
        const resolvedCard = document.querySelector('[data-complaint-stat="resolved"]');
        if (resolvedCard && data.resolved_complaints !== undefined) {
            this.animateNumber(resolvedCard, data.resolved_complaints);
        }
    }'''
    
    js_content = js_content.replace(old_update_summary, new_update_summary)
    
    # Add real-time complaint updates
    js_content += '''

// Real-time complaint updates for admin dashboard
function startComplaintRealTimeUpdates() {
    // Update complaint stats every 30 seconds
    setInterval(() => {
        fetch('/admin/complaints-stats')
            .then(response => response.json())
            .then(data => {
                if (data.success && window.dashboardManager) {
                    window.dashboardManager.updateComplaintCards(data.stats);
                }
            })
            .catch(error => console.log('Complaint stats update error:', error));
    }, 30000);
    
    // Update recent activity every 30 seconds
    setInterval(() => {
        fetch('/admin/refresh-activity')
            .then(response => response.json())
            .then(data => {
                if (data.success && window.dashboardManager) {
                    window.dashboardManager.updateDashboardData(data);
                }
            })
            .catch(error => console.log('Activity update error:', error));
    }, 30000);
}

// Auto-refresh complaint management page
function startComplaintPageAutoRefresh() {
    if (window.location.pathname.includes('/complaints')) {
        setInterval(() => {
            // Refresh complaint statistics
            fetch('/admin/complaints-stats')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Update statistics cards
                        updateComplaintStatsCards(data.stats);
                    }
                })
                .catch(error => console.log('Error updating complaint stats:', error));
        }, 30000);
    }
}

function updateComplaintStatsCards(stats) {
    // Update total complaints
    const totalCard = document.querySelector('.card-body h4');
    if (totalCard && stats.total_complaints !== undefined) {
        animateValue(totalCard, parseInt(totalCard.textContent), stats.total_complaints, 1000);
    }
    
    // Update status-specific cards
    const statusCards = {
        'pending': stats.pending_complaints,
        'investigating': stats.investigating_complaints,
        'resolved': stats.resolved_complaints
    };
    
    Object.keys(statusCards).forEach(status => {
        const card = document.querySelector(`.card:has(.badge:contains("${status}")) h4`);
        if (card && statusCards[status] !== undefined) {
            animateValue(card, parseInt(card.textContent), statusCards[status], 1000);
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

// Initialize real-time updates when page loads
document.addEventListener('DOMContentLoaded', () => {
    startComplaintRealTimeUpdates();
    startComplaintPageAutoRefresh();
});
'''
    
    with open('app/static/js/dashboard.js', 'w', encoding='utf-8') as f:
        f.write(js_content)
    
    print("Fixed complaint real-time data fetching!")
    print("\nChanges made:")
    print("1. Added complaint statistics to admin dashboard")
    print("2. Enhanced refresh_activity endpoint with complaint data")
    print("3. Fixed manage_complaints route with pagination and filters")
    print("4. Added missing complaint management routes")
    print("5. Added real-time complaint updates to dashboard JavaScript")
    print("6. Added auto-refresh for complaint statistics every 30 seconds")
    print("\nThe complaint feature will now fetch and display real-time data!")

if __name__ == "__main__":
    fix_complaint_realtime()
