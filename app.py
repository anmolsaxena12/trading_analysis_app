from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from flask_cors import CORS
import os
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta
import traceback
import numpy as np

from utils.kite_handler import KiteHandler
from utils.technical_analyzer import TechnicalAnalyzer
from utils.fundamental_analyzer import FundamentalAnalyzer
from utils.risk_manager import RiskManager
from utils.ai_analyzer import AIAnalyzer
from utils.portfolio_manager import PortfolioManager
from utils.stock_scanner import StockScanner

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')
CORS(app)

# Initialize components
kite_handler = None
technical_analyzer = TechnicalAnalyzer()
fundamental_analyzer = FundamentalAnalyzer()
risk_manager = RiskManager()
ai_analyzer = AIAnalyzer()
portfolio_manager = None

def initialize_handlers():
    global kite_handler, portfolio_manager
    # Kite integration is OPTIONAL - app works fine without it
    # Only needed for portfolio features (holdings, positions, order placement)
    try:
        kite_handler = KiteHandler()
        if kite_handler.is_connected():
            portfolio_manager = PortfolioManager(kite_handler)
            print("✓ Kite integration enabled - Portfolio features available")
        else:
            print("ℹ Kite not connected - Running in analysis-only mode (no portfolio features)")
            print("  Stock analysis, technical/fundamental analysis, and AI recommendations still available!")
    except Exception as e:
        print(f"ℹ Kite integration disabled: {e}")
        print("  App running in analysis-only mode - all analysis features still available!")

# Initialize handlers on startup
initialize_handlers()

# Initialize stock scanner (after all analyzers are ready)
stock_scanner = StockScanner(
    technical_analyzer, 
    fundamental_analyzer, 
    ai_analyzer, 
    risk_manager
)
print("✓ Stock scanner initialized - Buy recommendations available")

def convert_numpy_types(obj):
    """Convert NumPy types to Python native types for JSON serialization"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    return obj

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_stock():
    try:
        data = request.get_json()
        symbol = data.get('symbol', '').upper()

        if not symbol:
            return jsonify({'error': 'Symbol is required'}), 400

        # Get stock data
        stock_data = fundamental_analyzer.get_stock_data(symbol)
        if stock_data.empty:
            return jsonify({'error': 'Could not fetch stock data'}), 404

        # Technical Analysis
        technical_signals = technical_analyzer.analyze(stock_data)

        # Fundamental Analysis
        fundamental_data = fundamental_analyzer.analyze(symbol)

        # Current price and buying recommendation
        current_price = stock_data['Close'].iloc[-1]
        buying_analysis = ai_analyzer.analyze_buying_opportunity(
            symbol, current_price, technical_signals, fundamental_data
        )

        # Portfolio analysis if available
        portfolio_analysis = None
        if portfolio_manager and portfolio_manager.is_connected():
            try:
                portfolio_analysis = portfolio_manager.get_portfolio_analysis()
            except Exception as e:
                print(f"Portfolio analysis error: {e}")

        # Risk-reward analysis
        if buying_analysis.get('should_buy', False):
            risk_reward = risk_manager.calculate_risk_reward(
                current_price,
                buying_analysis.get('target_price', current_price * 1.1),
                buying_analysis.get('stop_loss', current_price * 0.95)
            )
        else:
            risk_reward = None

        # Generate position size recommendation
        position_recommendation = None
        if portfolio_manager and risk_reward and buying_analysis.get('should_buy', False):
            try:
                available_funds = portfolio_manager.get_available_funds()
                position_recommendation = risk_manager.calculate_position_size(
                    available_funds, current_price, risk_reward
                )
            except Exception as e:
                print(f"Position calculation error: {e}")

        response = {
            'symbol': symbol,
            'current_price': current_price,
            'technical_analysis': technical_signals,
            'fundamental_analysis': fundamental_data,
            'buying_analysis': buying_analysis,
            'risk_reward': risk_reward,
            'portfolio_analysis': portfolio_analysis,
            'position_recommendation': position_recommendation,
            'timestamp': datetime.now().isoformat()
        }

        return jsonify(response)

    except Exception as e:
        print(f"Analysis error: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/portfolio')
def portfolio():
    try:
        if not portfolio_manager or not portfolio_manager.is_connected():
            flash('Portfolio data not available. Please check Kite API connection.', 'warning')
            return render_template('portfolio.html', holdings=[], positions=[])

        holdings = portfolio_manager.get_holdings()
        positions = portfolio_manager.get_positions()

        return render_template('portfolio.html', holdings=holdings, positions=positions)
    except Exception as e:
        flash(f'Error fetching portfolio: {str(e)}', 'error')
        return render_template('portfolio.html', holdings=[], positions=[])

@app.route('/recommendations')
def recommendations():
    """Display buy recommendations page"""
    return render_template('recommendations.html')

@app.route('/api/recommendations', methods=['GET', 'POST'])
def get_recommendations():
    """API endpoint to get buy recommendations"""
    try:
        if request.method == 'POST':
            data = request.get_json() or {}
            symbols = data.get('symbols', None)
            min_score = data.get('min_score', 60)
            max_results = data.get('max_results', 20)
        else:
            symbols = request.args.get('symbols', None)
            min_score = int(request.args.get('min_score', 60))
            max_results = int(request.args.get('max_results', 20))
            
            if symbols:
                symbols = [s.strip().upper() for s in symbols.split(',')]
        
        recommendations = stock_scanner.scan_stocks(
            symbols=symbols,
            min_score=min_score,
            max_results=max_results
        )
        
        # Convert NumPy types to Python native types for JSON serialization
        recommendations = convert_numpy_types(recommendations)
        
        return jsonify({
            'recommendations': recommendations,
            'count': len(recommendations),
            'scanned_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Recommendations error: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/sell-recommendations')
def sell_recommendations():
    try:
        if not portfolio_manager or not portfolio_manager.is_connected():
            return jsonify({'error': 'Portfolio not available'}), 503

        recommendations = portfolio_manager.get_sell_recommendations()
        return jsonify(recommendations)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def api_status():
    status = {
        'kite_connected': kite_handler.is_connected() if kite_handler else False,
        'portfolio_available': portfolio_manager.is_connected() if portfolio_manager else False,
        'services': {
            'technical_analysis': True,
            'fundamental_analysis': True,
            'ai_analysis': ai_analyzer.is_available(),
            'risk_management': True
        }
    }
    return jsonify(status)

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)