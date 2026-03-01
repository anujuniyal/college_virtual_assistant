/**
 * Charts.js Helper Functions
 * Additional chart utilities for analytics dashboard
 */

function createBarChart(canvasId, data, labels) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Count',
                data: data,
                backgroundColor: '#667eea',
                borderColor: '#764ba2',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function createPieChart(canvasId, data, labels) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    return new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    '#667eea',
                    '#764ba2',
                    '#f093fb',
                    '#4facfe',
                    '#00f2fe'
                ]
            }]
        },
        options: {
            responsive: true
        }
    });
}

function updateCharts() {
    // Fetch latest analytics data and update charts
    fetch('/api/analytics')
        .then(response => response.json())
        .then(data => {
            // Update charts with new data
            console.log('Analytics data updated', data);
        })
        .catch(error => console.error('Error fetching analytics:', error));
}

// Auto-refresh charts every 5 minutes
setInterval(updateCharts, 300000);
