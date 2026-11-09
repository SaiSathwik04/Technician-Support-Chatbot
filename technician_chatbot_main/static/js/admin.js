// Admin dashboard functionality
class AdminDashboard {
    constructor() {
        this.charts = {};
        this.loadingModal = document.getElementById('loadingModal');
        this.loadingMessage = document.getElementById('loadingMessage');
        
        this.initializeEventListeners();
        this.startAutoRefresh();
    }
    
    initializeEventListeners() {
        // Real-time updates
        this.setupAutoRefresh();
        
        // Filter forms
        this.setupFilters();
        
        // Export buttons
        this.setupExportHandlers();
    }
    
    setupAutoRefresh() {
        // Refresh metrics every 30 seconds
        setInterval(() => {
            this.refreshMetrics();
        }, 30000);
        
        // Refresh charts every 60 seconds
        setInterval(() => {
            this.refreshCharts();
        }, 60000);
    }
    
    setupFilters() {
        const filterForms = document.querySelectorAll('.filter-form');
        filterForms.forEach(form => {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.applyFilters(form);
            });
        });
        
        // Auto-apply filters on change
        const filterInputs = document.querySelectorAll('.filter-input');
        filterInputs.forEach(input => {
            input.addEventListener('change', () => {
                this.debounce(() => {
                    const form = input.closest('.filter-form');
                    if (form) {
                        this.applyFilters(form);
                    }
                }, 500)();
            });
        });
    }
    
    setupExportHandlers() {
        const exportButtons = document.querySelectorAll('.export-btn');
        exportButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const exportType = button.dataset.export;
                this.exportData(exportType);
            });
        });
    }
    
    async refreshMetrics() {
        try {
            const response = await fetch('/admin/api/metrics/current', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to fetch metrics');
            }
            
            const data = await response.json();
            this.updateMetricsDisplay(data);
            
        } catch (error) {
            console.error('Error refreshing metrics:', error);
        }
    }
    
    async refreshCharts() {
        const chartTypes = ['daily_interactions', 'intent_distribution', 'source_distribution'];
        
        for (const chartType of chartTypes) {
            try {
                const response = await fetch(`/admin/api/metrics/chart_data?type=${chartType}&days=30`);
                const data = await response.json();
                
                if (data.success && this.charts[chartType]) {
                    this.updateChart(chartType, data.data);
                }
            } catch (error) {
                console.error(`Error updating ${chartType} chart:`, error);
            }
        }
    }
    
    updateMetricsDisplay(data) {
        // Update metric cards
        const metricElements = {
            'total_interactions': document.querySelector('[data-metric="total_interactions"]'),
            'recent_interactions': document.querySelector('[data-metric="recent_interactions"]'),
            'avg_confidence': document.querySelector('[data-metric="avg_confidence"]'),
            'avg_rating': document.querySelector('[data-metric="avg_rating"]')
        };
        
        Object.keys(metricElements).forEach(key => {
            const element = metricElements[key];
            if (element && data[key] !== undefined) {
                if (key === 'avg_confidence') {
                    element.textContent = `${(data[key] * 100).toFixed(1)}%`;
                } else if (key === 'avg_rating') {
                    element.textContent = data[key] ? `${data[key].toFixed(1)}/5` : 'N/A';
                } else {
                    element.textContent = data[key];
                }
            }
        });
        
        // Update last updated time
        const lastUpdated = document.querySelector('[data-metric="last_updated"]');
        if (lastUpdated) {
            lastUpdated.textContent = new Date().toLocaleTimeString();
        }
    }
    
    updateChart(chartType, newData) {
        const chart = this.charts[chartType];
        if (!chart) return;
        
        // Update chart data
        switch (chartType) {
            case 'daily_interactions':
                chart.data.labels = newData.map(item => item._id);
                chart.data.datasets[0].data = newData.map(item => item.count);
                break;
            case 'intent_distribution':
            case 'source_distribution':
                chart.data.labels = newData.map(item => item._id);
                chart.data.datasets[0].data = newData.map(item => item.count);
                break;
        }
        
        chart.update();
    }
    
    async applyFilters(form) {
        const formData = new FormData(form);
        const params = new URLSearchParams(formData);
        
        this.showLoading('Applying filters...');
        
        try {
            const response = await fetch(`${form.action}?${params}`, {
                method: 'GET'
            });
            
            if (!response.ok) {
                throw new Error('Failed to apply filters');
            }
            
            // Reload the page with new filters
            window.location.href = `${window.location.pathname}?${params}`;
            
        } catch (error) {
            console.error('Error applying filters:', error);
            this.showError('Failed to apply filters');
        } finally {
            this.hideLoading();
        }
    }
    
    async exportData(exportType) {
        this.showLoading('Preparing export...');
        
        try {
            const response = await fetch(`/admin/api/export/${exportType}`, {
                method: 'GET'
            });
            
            if (!response.ok) {
                throw new Error('Export failed');
            }
            
            // Handle file download
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${exportType}_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            this.showSuccess('Export completed successfully');
            
        } catch (error) {
            console.error('Export error:', error);
            this.showError('Export failed. Please try again.');
        } finally {
            this.hideLoading();
        }
    }
    
    showLoading(message = 'Processing...') {
        if (this.loadingMessage) {
            this.loadingMessage.textContent = message;
        }
        if (this.loadingModal) {
            this.loadingModal.classList.remove('hidden');
            this.loadingModal.classList.add('flex');
        }
    }
    
    hideLoading() {
        if (this.loadingModal) {
            this.loadingModal.classList.add('hidden');
            this.loadingModal.classList.remove('flex');
        }
    }
    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        const bgColor = type === 'success' ? 'bg-green-100 border-green-300 text-green-800' :
                        type === 'error' ? 'bg-red-100 border-red-300 text-red-800' :
                        'bg-blue-100 border-blue-300 text-blue-800';
        
        notification.className = `fixed top-4 right-4 ${bgColor} border px-4 py-3 rounded-md shadow-lg z-50 max-w-md`;
        notification.innerHTML = `
            <div class="flex items-center justify-between">
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-4 hover:opacity-75">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// System management functions
async function retrainModels() {
    if (!confirm('Are you sure you want to retrain the models? This may take a few minutes.')) {
        return;
    }
    
    adminDashboard.showLoading('Retraining models...');
    
    try {
        const response = await fetch('/admin/api/system/retrain', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            adminDashboard.showSuccess('Models retrained successfully!');
        } else {
            throw new Error(data.message || 'Retraining failed');
        }
        
    } catch (error) {
        console.error('Retraining error:', error);
        adminDashboard.showError('Failed to retrain models: ' + error.message);
    } finally {
        adminDashboard.hideLoading();
    }
}

async function reindexKnowledgeBase() {
    if (!confirm('Are you sure you want to reindex the knowledge base?')) {
        return;
    }
    
    adminDashboard.showLoading('Reindexing knowledge base...');
    
    try {
        const response = await fetch('/admin/api/system/reindex', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            adminDashboard.showSuccess('Knowledge base reindexed successfully!');
        } else {
            throw new Error(data.message || 'Reindexing failed');
        }
        
    } catch (error) {
        console.error('Reindexing error:', error);
        adminDashboard.showError('Failed to reindex knowledge base: ' + error.message);
    } finally {
        adminDashboard.hideLoading();
    }
}

function exportData() {
    if (adminDashboard) {
        adminDashboard.exportData('chat_logs');
    }
}

// Pagination helper
function goToPage(page) {
    const url = new URL(window.location);
    url.searchParams.set('page', page);
    window.location.href = url.toString();
}

// Table sorting helper
function sortTable(column, order = 'asc') {
    const url = new URL(window.location);
    url.searchParams.set('sort', column);
    url.searchParams.set('order', order);
    window.location.href = url.toString();
}

// Initialize admin dashboard
let adminDashboard;

document.addEventListener('DOMContentLoaded', function() {
    adminDashboard = new AdminDashboard();
    
    // Initialize tooltips
    const tooltips = document.querySelectorAll('[title]');
    tooltips.forEach(element => {
        element.addEventListener('mouseenter', function() {
            this.setAttribute('data-tooltip', this.getAttribute('title'));
            this.removeAttribute('title');
        });
        
        element.addEventListener('mouseleave', function() {
            this.setAttribute('title', this.getAttribute('data-tooltip'));
            this.removeAttribute('data-tooltip');
        });
    });
    
    // Initialize date pickers
    const datePickers = document.querySelectorAll('input[type="date"]');
    datePickers.forEach(picker => {
        if (!picker.value) {
            picker.valueAsDate = new Date();
        }
    });
    
    console.log('Admin dashboard initialized');
});

// Real-time updates using Server-Sent Events (optional)
class RealtimeUpdates {
    constructor() {
        this.eventSource = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }
    
    connect() {
        if (!window.EventSource) {
            console.warn('Server-Sent Events not supported');
            return;
        }
        
        try {
            this.eventSource = new EventSource('/admin/api/realtime');
            
            this.eventSource.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleRealtimeUpdate(data);
            };
            
            this.eventSource.onerror = () => {
                this.handleConnectionError();
            };
            
            this.eventSource.onopen = () => {
                this.reconnectAttempts = 0;
                console.log('Real-time updates connected');
            };
            
        } catch (error) {
            console.error('Failed to connect to real-time updates:', error);
        }
    }
    
    handleRealtimeUpdate(data) {
        switch (data.type) {
            case 'new_interaction':
                this.updateInteractionCount();
                break;
            case 'feedback_received':
                this.updateFeedbackMetrics();
                break;
            case 'system_status':
                this.updateSystemStatus(data.status);
                break;
        }
    }
    
    handleConnectionError() {
        if (this.eventSource) {
            this.eventSource.close();
        }
        
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.pow(2, this.reconnectAttempts) * 1000; // Exponential backoff
            
            console.log(`Reconnecting in ${delay/1000}s... (attempt ${this.reconnectAttempts})`);
            setTimeout(() => this.connect(), delay);
        } else {
            console.error('Max reconnection attempts reached');
        }
    }
    
    updateInteractionCount() {
        const element = document.querySelector('[data-metric="recent_interactions"]');
        if (element) {
            const current = parseInt(element.textContent) || 0;
            element.textContent = current + 1;
        }
    }
    
    updateFeedbackMetrics() {
        // Refresh feedback metrics
        if (adminDashboard) {
            adminDashboard.refreshMetrics();
        }
    }
    
    updateSystemStatus(status) {
        const statusElement = document.querySelector('[data-metric="system_status"]');
        if (statusElement) {
            statusElement.textContent = status;
            statusElement.className = status === 'online' ? 'text-green-600' : 'text-red-600';
        }
    }
    
    disconnect() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }
}

// Initialize real-time updates (optional feature)
const realtimeUpdates = new RealtimeUpdates();

// Connect to real-time updates when page is visible
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        realtimeUpdates.disconnect();
    } else {
        realtimeUpdates.connect();
    }
});

// Export for module use if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AdminDashboard, realtimeUpdates };
}
