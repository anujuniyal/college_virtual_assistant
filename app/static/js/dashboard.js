// Enhanced Dashboard JavaScript
class DashboardManager {
    constructor() {
        this.init();
        this.setupEventListeners();
        this.startAutoRefresh();
    }

    init() {
        // Initialize tooltips
        this.initTooltips();
        
        // Initialize sidebar state
        this.initSidebar();
        
        // Set up mobile menu
        this.initMobileMenu();
        
        // Initialize real-time updates
        this.initRealTimeUpdates();
    }

    initTooltips() {
        // Initialize Bootstrap tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    initSidebar() {
        // Check if sidebar should be collapsed
        const sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
        if (sidebarCollapsed) {
            document.querySelector('.sidebar').classList.add('collapsed');
        }

        // Add toggle button functionality
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'sidebar-toggle-btn';
        toggleBtn.innerHTML = '<i class="fas fa-bars"></i>';
        toggleBtn.onclick = () => this.toggleSidebar();
        
        const sidebar = document.querySelector('.sidebar');
        if (sidebar) {
            sidebar.insertBefore(toggleBtn, sidebar.firstChild);
        }
    }

    toggleSidebar() {
        const sidebar = document.querySelector('.sidebar');
        const mainContent = document.querySelector('.main-content');
        
        sidebar.classList.toggle('collapsed');
        
        const isCollapsed = sidebar.classList.contains('collapsed');
        localStorage.setItem('sidebarCollapsed', isCollapsed);
        
        // Adjust main content margin
        if (isCollapsed) {
            mainContent.style.marginLeft = '70px';
        } else {
            mainContent.style.marginLeft = '250px';
        }
    }

    initMobileMenu() {
        // Create mobile menu toggle button
        const mobileToggle = document.createElement('button');
        mobileToggle.className = 'mobile-menu-toggle';
        mobileToggle.innerHTML = '<i class="fas fa-bars"></i>';
        mobileToggle.onclick = () => this.toggleMobileMenu();
        
        document.body.appendChild(mobileToggle);
    }

    toggleMobileMenu() {
        const sidebar = document.querySelector('.sidebar');
        sidebar.classList.toggle('mobile-open');
    }

    initRealTimeUpdates() {
        // Set up WebSocket or polling for real-time updates
        this.setupWebSocket();
    }

    setupWebSocket() {
        // WebSocket implementation would go here
        // For now, we'll use polling
        console.log('Real-time updates initialized with polling');
    }

    setupEventListeners() {
        // Handle navigation clicks
        document.addEventListener('click', (e) => {
            if (e.target.closest('.nav-link')) {
                this.handleNavigationClick(e.target.closest('.nav-link'));
            }
        });

        // Handle form submissions
        document.addEventListener('submit', (e) => {
            if (e.target.closest('.dashboard-form')) {
                this.handleFormSubmit(e);
            }
        });

        // Handle window resize
        window.addEventListener('resize', () => {
            this.handleResize();
        });

        // Handle visibility change
        document.addEventListener('visibilitychange', () => {
            this.handleVisibilityChange();
        });
    }

    handleNavigationClick(navLink) {
        // Remove active class from all links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        
        // Add active class to clicked link
        navLink.classList.add('active');
        
        // Save current page
        localStorage.setItem('currentPage', navLink.getAttribute('href'));
    }

    handleFormSubmit(e) {
        e.preventDefault();
        const form = e.target;
        const submitBtn = form.querySelector('button[type="submit"]');
        
        // Show loading state
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="loading"></span> Processing...';
        }
        
        // Simulate form submission
        setTimeout(() => {
            this.showNotification('Form submitted successfully!', 'success');
            
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Submit';
            }
            
            form.reset();
        }, 2000);
    }

    handleResize() {
        // Handle responsive behavior
        if (window.innerWidth > 768) {
            const sidebar = document.querySelector('.sidebar');
            if (sidebar) {
                sidebar.classList.remove('mobile-open');
            }
        }
    }

    handleVisibilityChange() {
        // Pause/resume auto-refresh based on page visibility
        if (document.hidden) {
            this.stopAutoRefresh();
        } else {
            this.startAutoRefresh();
        }
    }

    startAutoRefresh() {
        // Clear existing interval
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        // Set up auto-refresh every 30 seconds
        this.refreshInterval = setInterval(() => {
            this.refreshDashboard();
        }, 30000);
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    refreshDashboard() {
        const dashboardUrl = document.body.getAttribute('data-dashboard-url');
        
        if (dashboardUrl) {
            fetch(dashboardUrl)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        this.updateDashboardData(data);
                    }
                })
                .catch(error => {
                    console.error('Error refreshing dashboard:', error);
                });
        }
    }

    updateDashboardData(data) {
        // Update summary cards
        this.updateSummaryCards(data);
        
        // Update recent activity
        if (data.recent_notifications) {
            this.updateRecentActivity(data.recent_notifications);
        }
        
        // Show update indicator
        this.showUpdateIndicator();
    }

    updateSummaryCards(data) {
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
    }

    animateNumber(element, targetNumber) {
        const startNumber = parseInt(element.textContent) || 0;
        const duration = 1000;
        const startTime = performance.now();
        
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const currentNumber = Math.floor(startNumber + (targetNumber - startNumber) * progress);
            element.textContent = currentNumber;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }

    updateRecentActivity(notifications) {
        const activityList = document.querySelector('.activity-list');
        if (!activityList) return;
        
        // Keep static items and update dynamic ones
        const staticItems = 3; // Number of static items to keep
        
        notifications.forEach((notif, index) => {
            const existingItem = activityList.children[staticItems + index];
            if (existingItem) {
                const textElement = existingItem.querySelector('.activity-text');
                const timeElement = existingItem.querySelector('.activity-time');
                
                if (textElement) textElement.textContent = notif.title;
                if (timeElement) timeElement.textContent = notif.created_at;
            }
        });
    }

    showUpdateIndicator() {
        // Show subtle indicator that data was updated
        const indicator = document.createElement('div');
        indicator.className = 'update-indicator';
        indicator.innerHTML = '<i class="fas fa-check-circle"></i> Data updated';
        indicator.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--success-color);
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

    showNotification(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.dashboard-content');
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

    // Utility methods
    formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    // Export functionality
    exportData(format = 'json') {
        this.showNotification(`Preparing ${format.toUpperCase()} export...`, 'info');
        
        setTimeout(() => {
            this.showNotification(`Data exported successfully as ${format.toUpperCase()}!`, 'success');
        }, 2000);
    }

    // Print functionality
    printDashboard() {
        window.print();
    }

    // Theme switching (if needed)
    toggleTheme() {
        document.body.classList.toggle('dark-theme');
        const isDark = document.body.classList.contains('dark-theme');
        localStorage.setItem('darkTheme', isDark);
        this.showNotification(`Switched to ${isDark ? 'dark' : 'light'} theme`, 'info');
    }
}

// Global functions for template compatibility
function toggleSubmenu(element) {
    const submenu = element.nextElementSibling;
    if (submenu && submenu.classList.contains('submenu')) {
        submenu.classList.toggle('show');
        const icon = element.querySelector('.fa-chevron-down');
        if (icon) {
            icon.style.transform = submenu.classList.contains('show') ? 'rotate(180deg)' : 'rotate(0deg)';
        }
    }
}

function refreshActivity() {
    if (window.dashboardManager) {
        window.dashboardManager.refreshDashboard();
    }
}

function showNotification(message, type) {
    if (window.dashboardManager) {
        window.dashboardManager.showNotification(message, type);
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.dashboardManager = new DashboardManager();
    
    // Set active navigation based on current page
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
    
    // Restore last visited page
    const lastPage = localStorage.getItem('currentPage');
    if (lastPage && lastPage !== currentPath) {
        console.log('Last visited page:', lastPage);
    }
});

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
    
    .sidebar-toggle-btn {
        background: none;
        border: none;
        color: white;
        padding: 10px;
        cursor: pointer;
        font-size: 1.2rem;
        margin: 10px;
        border-radius: 5px;
        transition: background 0.3s ease;
    }
    
    .sidebar-toggle-btn:hover {
        background: rgba(255,255,255,0.1);
    }
    
    .loading {
        display: inline-block;
        width: 16px;
        height: 16px;
        border: 2px solid #f3f3f3;
        border-top: 2px solid currentColor;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);


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
