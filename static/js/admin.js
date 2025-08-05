/* YouTube API Server - Admin Panel JavaScript */

class AdminDashboard {
    constructor() {
        this.updateInterval = 30000; // 30 seconds
        this.concurrentUsersUpdateInterval = 10000; // 10 seconds
        this.refreshTimer = null;
        this.concurrentUsersTimer = null;
        this.charts = {};
        this.socketConnected = false;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.startRealTimeUpdates();
        this.setupTooltips();
        this.setupChartAutoRefresh();
        
        console.log('Admin Dashboard initialized');
    }
    
    setupEventListeners() {
        // Page visibility change handler
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopRealTimeUpdates();
            } else {
                this.startRealTimeUpdates();
            }
        });
        
        // Window focus/blur handlers
        window.addEventListener('focus', () => {
            this.startRealTimeUpdates();
        });
        
        window.addEventListener('blur', () => {
            this.stopRealTimeUpdates();
        });
        
        // Form validation
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', this.handleFormSubmit.bind(this));
        });
        
        // API key copy buttons
        document.querySelectorAll('[data-copy]').forEach(button => {
            button.addEventListener('click', this.copyToClipboard.bind(this));
        });
        
        // Auto-refresh controls
        const refreshButtons = document.querySelectorAll('[data-refresh]');
        refreshButtons.forEach(button => {
            button.addEventListener('click', () => {
                this.refreshDashboardData();
            });
        });
    }
    
    startRealTimeUpdates() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }
        
        if (this.concurrentUsersTimer) {
            clearInterval(this.concurrentUsersTimer);
        }
        
        // Update concurrent users more frequently
        this.updateConcurrentUsers();
        this.concurrentUsersTimer = setInterval(() => {
            this.updateConcurrentUsers();
        }, this.concurrentUsersUpdateInterval);
        
        // Update full dashboard data less frequently
        this.refreshTimer = setInterval(() => {
            this.refreshDashboardData();
        }, this.updateInterval);
        
        console.log('Real-time updates started');
    }
    
    stopRealTimeUpdates() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
        
        if (this.concurrentUsersTimer) {
            clearInterval(this.concurrentUsersTimer);
            this.concurrentUsersTimer = null;
        }
        
        console.log('Real-time updates stopped');
    }
    
    async updateConcurrentUsers() {
        try {
            const response = await fetch('/admin/api/stats');
            const data = await response.json();
            
            if (data.status) {
                this.updateConcurrentUserDisplay(data.concurrent_users);
                this.updateFooterConcurrentUsers(data.concurrent_users);
                
                // Update cache hit rate if available
                if (data.cache_hit_rate !== undefined) {
                    this.updateCacheHitRate(data.cache_hit_rate);
                }
                
                // Update hourly requests if available
                if (data.hourly_requests !== undefined) {
                    this.updateHourlyRequests(data.hourly_requests);
                }
            }
        } catch (error) {
            console.error('Failed to update concurrent users:', error);
            this.showToast('Failed to update real-time data', 'error');
        }
    }
    
    updateConcurrentUserDisplay(count) {
        const elements = [
            document.getElementById('concurrent-users-count'),
            document.getElementById('live-users'),
            document.querySelector('[data-concurrent-users]')
        ];
        
        elements.forEach(element => {
            if (element) {
                const oldValue = parseInt(element.textContent) || 0;
                element.textContent = count;
                
                // Add animation for significant changes
                if (Math.abs(count - oldValue) > 5) {
                    element.classList.add('badge-pulse');
                    setTimeout(() => {
                        element.classList.remove('badge-pulse');
                    }, 2000);
                }
            }
        });
    }
    
    updateFooterConcurrentUsers(count) {
        const footerElement = document.getElementById('concurrent-users');
        if (footerElement) {
            footerElement.innerHTML = `<span class="live-indicator"></span>${count} concurrent users`;
        }
    }
    
    updateCacheHitRate(rate) {
        const element = document.querySelector('[data-cache-hit-rate]');
        if (element) {
            element.textContent = `${rate}%`;
        }
    }
    
    updateHourlyRequests(requests) {
        const element = document.querySelector('[data-hourly-requests]');
        if (element) {
            element.textContent = requests;
        }
    }
    
    async refreshDashboardData() {
        try {
            this.showLoading(true);
            
            // Simulate API call for full dashboard refresh
            // In a real implementation, this would fetch updated analytics data
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            this.showLoading(false);
            this.showToast('Dashboard data refreshed', 'success');
            
        } catch (error) {
            console.error('Failed to refresh dashboard:', error);
            this.showLoading(false);
            this.showToast('Failed to refresh dashboard data', 'error');
        }
    }
    
    showLoading(show) {
        const loadingElements = document.querySelectorAll('[data-loading]');
        loadingElements.forEach(element => {
            if (show) {
                element.classList.add('loading-skeleton');
            } else {
                element.classList.remove('loading-skeleton');
            }
        });
    }
    
    copyToClipboard(event) {
        const button = event.currentTarget;
        const textToCopy = button.getAttribute('data-copy') || button.previousElementSibling.textContent;
        
        navigator.clipboard.writeText(textToCopy).then(() => {
            this.showToast('Copied to clipboard!', 'success');
            
            // Visual feedback
            const originalIcon = button.innerHTML;
            button.innerHTML = '<i data-feather="check" style="width: 14px; height: 14px;"></i>';
            feather.replace();
            
            setTimeout(() => {
                button.innerHTML = originalIcon;
                feather.replace();
            }, 2000);
            
        }).catch(error => {
            console.error('Failed to copy to clipboard:', error);
            this.showToast('Failed to copy to clipboard', 'error');
        });
    }
    
    handleFormSubmit(event) {
        const form = event.target;
        const submitButton = form.querySelector('button[type="submit"]');
        
        if (submitButton) {
            const originalText = submitButton.innerHTML;
            submitButton.innerHTML = '<i data-feather="loader" class="me-1"></i>Processing...';
            submitButton.disabled = true;
            feather.replace();
            
            // Re-enable button after form submission
            setTimeout(() => {
                submitButton.innerHTML = originalText;
                submitButton.disabled = false;
                feather.replace();
            }, 3000);
        }
    }
    
    showToast(message, type = 'info', duration = 5000) {
        // Create toast container if it doesn't exist
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }
        
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast show toast-${type}`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="toast-header">
                <i data-feather="${this.getToastIcon(type)}" class="me-2"></i>
                <strong class="me-auto">${this.getToastTitle(type)}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        container.appendChild(toast);
        feather.replace();
        
        // Auto-remove toast
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, duration);
        
        // Manual close functionality
        const closeButton = toast.querySelector('.btn-close');
        closeButton.addEventListener('click', () => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        });
    }
    
    getToastIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'alert-circle',
            warning: 'alert-triangle',
            info: 'info'
        };
        return icons[type] || 'info';
    }
    
    getToastTitle(type) {
        const titles = {
            success: 'Success',
            error: 'Error',
            warning: 'Warning',
            info: 'Information'
        };
        return titles[type] || 'Notification';
    }
    
    setupTooltips() {
        // Initialize Bootstrap tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    setupChartAutoRefresh() {
        // Auto-refresh charts every 5 minutes
        setInterval(() => {
            this.refreshCharts();
        }, 300000); // 5 minutes
    }
    
    refreshCharts() {
        // Refresh Chart.js charts if they exist
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.update === 'function') {
                chart.update('none'); // Update without animation
            }
        });
    }
    
    // Utility function to format numbers
    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }
    
    // Utility function to format bytes
    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    // Performance monitoring
    measurePerformance(label, fn) {
        const start = performance.now();
        const result = fn();
        const end = performance.now();
        
        console.log(`${label} took ${(end - start).toFixed(2)} milliseconds`);
        return result;
    }
}

// Global utility functions
window.updateConcurrentUsers = function(count) {
    const element = document.getElementById('concurrent-users');
    if (element) {
        element.innerHTML = `<span class="live-indicator"></span>${count} concurrent users`;
    }
};

window.refreshStats = function() {
    if (window.adminDashboard) {
        window.adminDashboard.refreshDashboardData();
    }
};

window.copyToClipboard = function(text) {
    navigator.clipboard.writeText(text).then(() => {
        if (window.adminDashboard) {
            window.adminDashboard.showToast('API key copied to clipboard!', 'success');
        }
    }).catch(error => {
        console.error('Failed to copy:', error);
        if (window.adminDashboard) {
            window.adminDashboard.showToast('Failed to copy to clipboard', 'error');
        }
    });
};

window.confirmDelete = function(keyId, keyName) {
    if (confirm(`Are you sure you want to delete the API key "${keyName}"? This action cannot be undone.`)) {
        // Submit the delete form
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/admin/api-keys/${keyId}/delete`;
        document.body.appendChild(form);
        form.submit();
    }
};

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Feather icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
    
    // Initialize admin dashboard
    window.adminDashboard = new AdminDashboard();
    
    // Setup global error handling
    window.addEventListener('error', function(event) {
        console.error('Global error:', event.error);
        if (window.adminDashboard) {
            window.adminDashboard.showToast('An unexpected error occurred', 'error');
        }
    });
    
    // Setup unhandled promise rejection handling
    window.addEventListener('unhandledrejection', function(event) {
        console.error('Unhandled promise rejection:', event.reason);
        if (window.adminDashboard) {
            window.adminDashboard.showToast('An unexpected error occurred', 'error');
        }
    });
    
    console.log('Admin Panel JavaScript loaded successfully');
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AdminDashboard;
}
