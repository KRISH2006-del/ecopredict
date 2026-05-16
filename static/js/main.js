/**
 * Main Application Entry Point
 * Imports and orchestrates all modules
 */

import { ChartManager } from './charts.js';
import { ApiService } from './api.js';
import { UIManager } from './ui.js';

// Initialize modules
const chartManager = new ChartManager();
const api = new ApiService();
const ui = new UIManager();

// Store for prediction visualization
let predictionChart = null;
let gaugeChart = null;

// DOM Ready Handler
document.addEventListener('DOMContentLoaded', async () => {
    console.log('EcoPredict App Initialized');

    // Initialize Prediction Form (if on predict page)
    initPredictionForm();

    // Initialize Dashboard Charts (if on dashboard page)
    await initDashboard();

    // Add ripple effect to buttons
    initRippleEffects();

    // Initialize tooltips
    initTooltips();
});

/**
 * Initialize prediction form handling
 */
function initPredictionForm() {
    const predictForm = document.getElementById('predictForm');
    if (!predictForm) return;

    // Set default date
    const dateInput = document.getElementById('date');
    if (dateInput) {
        dateInput.valueAsDate = new Date();
    }

    // Real-time validation
    const inputs = predictForm.querySelectorAll('select, input');
    inputs.forEach(input => {
        input.addEventListener('change', () => validateField(input));
        input.addEventListener('blur', () => validateField(input));
    });

    predictForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Validate all fields
        let isValid = true;
        inputs.forEach(input => {
            if (!validateField(input)) isValid = false;
        });

        if (!isValid) {
            ui.showToast('Please fill in all required fields', 'error');
            return;
        }

        const resultDiv = document.getElementById('result');
        const btn = e.target.querySelector('button');
        const vizSection = document.getElementById('visualization-section');

        ui.setButtonLoading(btn, true);
        resultDiv.className = '';

        try {
            // Show loading state
            await new Promise(r => setTimeout(r, 400));

            const formData = new FormData(e.target);
            const data = await api.predict(formData);

            if (data.error) {
                ui.showResult(resultDiv, `Error: ${data.error}`, false);
                if (vizSection) vizSection.classList.add('hidden');
                shakeElement(btn);
            } else {
                ui.showResult(
                    resultDiv,
                    `Estimated Waste Generation:<span>${data.prediction}</span>`,
                    true
                );
                ui.showToast('Prediction saved successfully', 'success');

                // Celebrate with button animation
                celebrateButton(btn);

                // Show and render visualization
                if (vizSection && data.comparison) {
                    vizSection.classList.remove('hidden');
                    renderPredictionVisualization(data);
                }
            }
        } catch (err) {
            ui.showResult(resultDiv, 'Server Connection Failed', false);
            shakeElement(btn);
        } finally {
            ui.setButtonLoading(btn, false);
        }
    });
}

/**
 * Validate a form field
 */
function validateField(input) {
    const formGroup = input.closest('.form-group');
    const value = input.value.trim();

    if (!value) {
        formGroup.classList.remove('valid');
        formGroup.classList.add('invalid');
        return false;
    } else {
        formGroup.classList.remove('invalid');
        formGroup.classList.add('valid');
        return true;
    }
}

/**
 * Shake an element to indicate error
 */
function shakeElement(element) {
    element.style.animation = 'shake 0.5s ease';
    setTimeout(() => element.style.animation = '', 500);
}

/**
 * Celebrate successful action
 */
function celebrateButton(button) {
    button.style.animation = 'celebrate 0.6s ease';
    setTimeout(() => button.style.animation = '', 600);
}

/**
 * Initialize ripple effects on buttons
 */
function initRippleEffects() {
    const buttons = document.querySelectorAll('button');
    buttons.forEach(btn => {
        btn.classList.add('ripple');
        btn.addEventListener('click', createRipple);
    });
}

function createRipple(e) {
    const button = e.currentTarget;
    const circle = document.createElement('span');
    const diameter = Math.max(button.clientWidth, button.clientHeight);
    const radius = diameter / 2;

    const rect = button.getBoundingClientRect();
    circle.style.width = circle.style.height = `${diameter}px`;
    circle.style.left = `${e.clientX - rect.left - radius}px`;
    circle.style.top = `${e.clientY - rect.top - radius}px`;
    circle.classList.add('ripple-effect');

    const ripple = button.querySelector('.ripple-effect');
    if (ripple) ripple.remove();

    button.appendChild(circle);
    setTimeout(() => circle.remove(), 600);
}

/**
 * Initialize tooltips
 */
function initTooltips() {
    // Add tooltips to elements with data-tooltip attribute
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    tooltipElements.forEach(el => el.classList.add('tooltip'));
}

/**
 * Render prediction visualization charts
 */
function renderPredictionVisualization(data) {
    const predValue = data.prediction_value;
    const comparison = data.comparison;

    // Animate stat values
    animateValue('pred-value', 0, predValue, 1000, ' kg');
    animateValue('area-avg', 0, comparison.area_avg, 1000, ' kg');
    animateValue('overall-avg', 0, comparison.overall_avg, 1000, ' kg');

    // Update gauge value display
    document.getElementById('gaugeValue').textContent = `${predValue.toLocaleString()} kg`;

    // Render Gauge Chart
    renderGaugeChart(predValue, comparison);

    // Render Comparison Bar Chart
    renderComparisonChart(predValue, comparison, data.labels);
}

/**
 * Animate a number from start to end
 */
function animateValue(elementId, start, end, duration, suffix = '') {
    const element = document.getElementById(elementId);
    if (!element) return;

    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 4); // easeOutQuart
        const current = Math.round(start + (end - start) * eased);
        element.textContent = current.toLocaleString() + suffix;

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

/**
 * Render a doughnut chart styled as a gauge
 */
function renderGaugeChart(value, comparison) {
    const ctx = document.getElementById('gaugeChart');
    if (!ctx) return;

    if (gaugeChart) gaugeChart.destroy();

    const maxVal = Math.max(value, comparison.area_avg, comparison.overall_avg) * 1.2;
    const percentage = (value / maxVal) * 100;

    let color = '#27ae60';
    if (value > comparison.area_avg * 1.1) color = '#f39c12';
    if (value > comparison.area_avg * 1.3) color = '#e74c3c';

    gaugeChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [percentage, 100 - percentage],
                backgroundColor: [color, 'rgba(255,255,255,0.1)'],
                borderWidth: 0,
                circumference: 180,
                rotation: 270
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '75%',
            animation: {
                animateRotate: true,
                duration: 1000,
                easing: 'easeOutQuart'
            },
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false }
            }
        }
    });
}

/**
 * Render comparison bar chart
 */
function renderComparisonChart(value, comparison, labels) {
    const ctx = document.getElementById('comparisonChart');
    if (!ctx) return;

    if (predictionChart) predictionChart.destroy();

    predictionChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Your Prediction', `${labels.area} Avg`, 'Overall Avg'],
            datasets: [{
                data: [value, comparison.area_avg, comparison.overall_avg],
                backgroundColor: [
                    'rgba(39, 174, 96, 0.8)',
                    'rgba(52, 152, 219, 0.8)',
                    'rgba(155, 89, 182, 0.8)'
                ],
                borderColor: [
                    'rgba(39, 174, 96, 1)',
                    'rgba(52, 152, 219, 1)',
                    'rgba(155, 89, 182, 1)'
                ],
                borderWidth: 2,
                borderRadius: 8
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 1000,
                easing: 'easeOutQuart'
            },
            plugins: {
                legend: { display: false },
                title: {
                    display: true,
                    text: 'Comparison with Historical Averages',
                    color: '#fff',
                    font: { size: 14, weight: '600' }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255,255,255,0.1)' },
                    ticks: { color: 'rgba(255,255,255,0.7)' }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: 'rgba(255,255,255,0.7)' }
                }
            }
        }
    });
}

/**
 * Initialize dashboard with charts
 */
async function initDashboard() {
    const dashboardContainer = document.getElementById('dashboard');
    if (!dashboardContainer) return;

    try {
        const stats = await api.getStats();

        // Animate stat cards
        animateValue('total-predictions', 0, stats.total_predictions, 1500);
        animateValue('avg-prediction', 0, Math.round(stats.avg_prediction), 1500);

        // Render charts with delay for staggered animation
        await new Promise(r => setTimeout(r, 300));

        if (stats.by_area.length > 0) {
            chartManager.createAreaChart('areaChart', stats.by_area);
            await new Promise(r => setTimeout(r, 200));
            chartManager.createDoughnutChart('distributionChart', stats.by_area);
        }

        await new Promise(r => setTimeout(r, 200));

        if (stats.by_date.length > 0) {
            chartManager.createTimelineChart('timelineChart', stats.by_date);
        }

    } catch (error) {
        console.error('Dashboard initialization failed:', error);
        ui.showToast('Failed to load dashboard data', 'error');
    }
}

// Add CSS for additional animations
const style = document.createElement('style');
style.textContent = `
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
        20%, 40%, 60%, 80% { transform: translateX(5px); }
    }
    
    @keyframes celebrate {
        0% { transform: scale(1); }
        25% { transform: scale(1.05); }
        50% { transform: scale(0.95); }
        75% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }
    
    .ripple-effect {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.4);
        transform: scale(0);
        animation: rippleAnimation 0.6s linear;
        pointer-events: none;
    }
    
    @keyframes rippleAnimation {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Export for potential external use
window.EcoPredict = { chartManager, api, ui };
