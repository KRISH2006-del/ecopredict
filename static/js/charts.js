/**
 * Chart Module - Handles all Chart.js visualizations
 * Uses ES6 module pattern
 */

export class ChartManager {
    constructor() {
        this.charts = {};
    }

    /**
     * Create a bar chart for predictions by area
     */
    createAreaChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }

        this.charts[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(d => d.area),
                datasets: [{
                    label: 'Average Prediction (kg)',
                    data: data.map(d => d.avg_weight),
                    backgroundColor: 'rgba(39, 174, 96, 0.7)',
                    borderColor: 'rgba(39, 174, 96, 1)',
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: 'Average Predictions by Area',
                        font: { size: 16, weight: '600' }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(0,0,0,0.05)' }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });

        return this.charts[canvasId];
    }

    /**
     * Create a line chart for predictions over time
     */
    createTimelineChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }

        // Reverse to show oldest to newest
        const sortedData = [...data].reverse();

        this.charts[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: sortedData.map(d => d.date),
                datasets: [{
                    label: 'Total Waste (kg)',
                    data: sortedData.map(d => d.total_weight),
                    fill: true,
                    backgroundColor: 'rgba(26, 188, 156, 0.2)',
                    borderColor: 'rgba(26, 188, 156, 1)',
                    borderWidth: 3,
                    tension: 0.4,
                    pointBackgroundColor: 'white',
                    pointBorderColor: 'rgba(26, 188, 156, 1)',
                    pointBorderWidth: 2,
                    pointRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: 'Prediction Trends Over Time',
                        font: { size: 16, weight: '600' }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(0,0,0,0.05)' }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });

        return this.charts[canvasId];
    }

    /**
     * Create a doughnut chart for waste type distribution
     */
    createDoughnutChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }

        const colors = [
            'rgba(46, 204, 113, 0.8)',
            'rgba(52, 152, 219, 0.8)',
            'rgba(155, 89, 182, 0.8)',
            'rgba(241, 196, 15, 0.8)',
            'rgba(230, 126, 34, 0.8)'
        ];

        this.charts[canvasId] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.map(d => d.area),
                datasets: [{
                    data: data.map(d => d.count),
                    backgroundColor: colors.slice(0, data.length),
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    title: {
                        display: true,
                        text: 'Predictions by Area',
                        font: { size: 16, weight: '600' }
                    }
                }
            }
        });

        return this.charts[canvasId];
    }
}

export default ChartManager;
