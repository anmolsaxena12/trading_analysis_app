// Trading Analysis App - JavaScript Functions

// Global variables
let currentAnalysis = null;
let apiStatus = {
    kite: false,
    portfolio: false,
    ai: false
};

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();

    // Auto-fill symbol from URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    const symbol = urlParams.get('symbol');
    if (symbol) {
        document.getElementById('stockSymbol').value = symbol;
        analyzeStock(symbol);
    }
});

function initializeApp() {
    // Check API status
    checkApiStatus();

    // Set up event listeners
    setupEventListeners();

    // Initialize tooltips
    initializeTooltips();
}

function setupEventListeners() {
    // Form submission
    const analysisForm = document.getElementById('analysisForm');
    if (analysisForm) {
        analysisForm.addEventListener('submit', handleFormSubmission);
    }

    // Symbol input auto-completion
    const symbolInput = document.getElementById('stockSymbol');
    if (symbolInput) {
        symbolInput.addEventListener('input', handleSymbolInput);
        symbolInput.addEventListener('keyup', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                analysisForm.dispatchEvent(new Event('submit'));
            }
        });
    }
}

function initializeTooltips() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

function handleFormSubmission(e) {
    e.preventDefault();
    const symbol = document.getElementById('stockSymbol').value.trim().toUpperCase();
    if (symbol) {
        analyzeStock(symbol);
    }
}

function handleSymbolInput(e) {
    // Convert to uppercase
    e.target.value = e.target.value.toUpperCase();

    // Basic validation
    const value = e.target.value;
    const isValid = /^[A-Z0-9&-]*$/.test(value);

    if (!isValid) {
        e.target.classList.add('is-invalid');
    } else {
        e.target.classList.remove('is-invalid');
    }
}

// API Status Management
function checkApiStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            apiStatus.kite = data.kite_connected;
            apiStatus.portfolio = data.portfolio_available;
            apiStatus.ai = data.services.ai_analysis;

            updateStatusIndicators(data);
        })
        .catch(error => {
            console.error('Error checking API status:', error);
            updateStatusIndicators({
                kite_connected: false,
                portfolio_available: false,
                services: { ai_analysis: false }
            });
        });
}

function updateStatusIndicators(data) {
    updateStatusBadge('kiteStatus', data.kite_connected, 'Kite API');
    updateStatusBadge('portfolioStatus', data.portfolio_available, 'Portfolio');
    updateStatusBadge('aiStatus', data.services.ai_analysis, 'AI Analysis');
}

function updateStatusBadge(elementId, isAvailable, service) {
    const element = document.getElementById(elementId);
    if (!element) return;

    if (isAvailable) {
        element.className = 'badge bg-success';
        element.textContent = 'Connected';
        element.title = `${service} is available`;
    } else {
        element.className = 'badge bg-warning';
        element.textContent = 'Unavailable';
        element.title = `${service} is not available`;
    }
}

// Stock Analysis Functions
function analyzeStock(symbol) {
    if (!symbol) return;

    // Show loading state
    showLoadingState();

    // Clear previous results
    hideResults();
    hideError();

    // Make API request
    fetch('/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({symbol: symbol})
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showError(data.error);
        } else {
            currentAnalysis = data;
            displayResults(data);
        }
    })
    .catch(error => {
        console.error('Analysis Error:', error);
        showError('Network error occurred. Please check your connection and try again.');
    })
    .finally(() => {
        hideLoadingState();
    });
}

function showLoadingState() {
    const loadingSpinner = document.getElementById('loadingSpinner');
    const analyzeBtn = document.getElementById('analyzeBtn');

    if (loadingSpinner) loadingSpinner.style.display = 'block';
    if (analyzeBtn) {
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Analyzing...';
    }
}

function hideLoadingState() {
    const loadingSpinner = document.getElementById('loadingSpinner');
    const analyzeBtn = document.getElementById('analyzeBtn');

    if (loadingSpinner) loadingSpinner.style.display = 'none';
    if (analyzeBtn) {
        analyzeBtn.disabled = false;
        analyzeBtn.innerHTML = '<i class="fas fa-chart-line me-2"></i>Analyze Stock';
    }
}

function showResults() {
    const resultsArea = document.getElementById('resultsArea');
    if (resultsArea) resultsArea.style.display = 'block';
}

function hideResults() {
    const resultsArea = document.getElementById('resultsArea');
    if (resultsArea) resultsArea.style.display = 'none';
}

function showError(message) {
    const errorDisplay = document.getElementById('errorDisplay');
    const errorMessage = document.getElementById('errorMessage');

    if (errorDisplay && errorMessage) {
        errorMessage.textContent = message;
        errorDisplay.style.display = 'block';
    }
}

function hideError() {
    const errorDisplay = document.getElementById('errorDisplay');
    if (errorDisplay) errorDisplay.style.display = 'none';
}

// Results Display Functions
function displayResults(data) {
    showResults();

    // Update basic info
    updateStockInfo(data);

    // Update recommendation
    updateRecommendation(data.buying_analysis);

    // Display technical analysis
    displayTechnicalAnalysis(data.technical_analysis);

    // Display fundamental analysis  
    displayFundamentalAnalysis(data.fundamental_analysis);

    // Display risk management
    if (data.risk_reward || data.position_recommendation) {
        displayRiskManagement(data.risk_reward, data.position_recommendation);
    }

    // Display AI analysis
    if (data.buying_analysis) {
        displayAIAnalysis(data.buying_analysis);
    }
}

function updateStockInfo(data) {
    const stockTitle = document.getElementById('stockTitle');
    const currentPrice = document.getElementById('currentPrice');

    if (stockTitle) {
        stockTitle.textContent = `${data.symbol} Analysis Results`;
    }

    if (currentPrice) {
        currentPrice.textContent = `₹${formatNumber(data.current_price, 2)}`;
    }
}

function updateRecommendation(analysis) {
    const recommendationElement = document.getElementById('recommendation');
    if (!recommendationElement || !analysis) return;

    const shouldBuy = analysis.should_buy;
    const confidence = analysis.confidence_level || 'Medium';

    const badgeClass = shouldBuy ? 'bg-success' : 'bg-danger';
    const recText = shouldBuy ? 'BUY' : 'HOLD/AVOID';

    recommendationElement.innerHTML = `
        <span class="badge ${badgeClass} fs-6">${recText}</span>
        <small class="text-muted ms-2">(${confidence} confidence)</small>
    `;
}

// Utility Functions
function formatNumber(num, decimals = 2) {
    if (num === null || num === undefined || isNaN(num)) return 'N/A';
    return Number(num).toLocaleString('en-IN', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

function formatPercentage(num, decimals = 2) {
    if (num === null || num === undefined || isNaN(num)) return 'N/A';
    return formatNumber(num, decimals) + '%';
}

function formatCurrency(num, symbol = '₹') {
    if (num === null || num === undefined || isNaN(num)) return 'N/A';
    return symbol + formatNumber(num, 2);
}

function getBadgeClass(value, thresholds = {good: 70, fair: 40}) {
    if (value >= thresholds.good) return 'bg-success';
    if (value >= thresholds.fair) return 'bg-warning';
    return 'bg-danger';
}

function getSignalBadgeClass(signal) {
    switch(signal) {
        case 'BUY': return 'bg-success';
        case 'SELL': return 'bg-danger';
        case 'HOLD': return 'bg-secondary';
        default: return 'bg-secondary';
    }
}

// Chart Functions (if needed for future enhancements)
function createChart(containerId, data, type = 'line') {
    // Placeholder for chart creation using Plotly.js
    // Can be expanded based on requirements
    console.log('Chart creation placeholder', containerId, data, type);
}

// Export functions for global use
window.analyzeStock = analyzeStock;
window.checkApiStatus = checkApiStatus;
window.formatNumber = formatNumber;
window.formatPercentage = formatPercentage;
window.formatCurrency = formatCurrency;

// Portfolio specific functions
function loadSellRecommendations() {
    const button = event.target;
    const originalText = button.innerHTML;

    // Show loading state
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
    button.disabled = true;

    fetch('/sell-recommendations')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showNotification('Error loading recommendations: ' + data.error, 'error');
            } else {
                displaySellRecommendations(data);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Failed to load sell recommendations', 'error');
        })
        .finally(() => {
            button.innerHTML = originalText;
            button.disabled = false;
        });
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 1050; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(notification);

    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Make functions globally available
window.loadSellRecommendations = loadSellRecommendations;
window.showNotification = showNotification;