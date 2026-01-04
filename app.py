from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from flask_cors import CORS
import os
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta
import traceback
import numpy as np

from utils.kite_handler import KiteHandler
from agents.orchestrator import AgentOrchestrator

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')
CORS(app)

# Initialize components
kite_handler = None
agent_orchestrator = None

def initialize_handlers():
    global kite_handler, agent_orchestrator
    # Kite integration is OPTIONAL - app works fine without it
    # Only needed for portfolio features (holdings, positions, order placement)
    try:
        kite_handler = KiteHandler()
        if kite_handler.is_connected():
            print("✓ Kite integration enabled - Portfolio features available")
        else:
            print("ℹ Kite not connected - Running in analysis-only mode (no portfolio features)")
            print("  Stock analysis, technical/fundamental analysis, and AI recommendations still available!")
    except Exception as e:
        print(f"ℹ Kite integration disabled: {e}")
        print("  App running in analysis-only mode - all analysis features still available!")
    
    # Initialize Multi-Agent Orchestrator with MCP
    agent_orchestrator = AgentOrchestrator(kite_handler)
    print("✓ Multi-Agent System initialized with MCP")

# Initialize handlers on startup
initialize_handlers()

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
    """Landing page - Sector-wise stock analysis"""
    return render_template('sector_analysis.html')

@app.route('/analyze-stock')
def analyze_stock_page():
    """Individual stock analysis page"""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_stock():
    try:
        data = request.get_json()
        symbol = data.get('symbol', '').upper()

        if not symbol:
            return jsonify({'error': 'Symbol is required'}), 400

        # Use Multi-Agent Orchestrator for analysis
        result = agent_orchestrator.analyze_stock(symbol)
        
        if 'error' in result:
            return jsonify(result), 500
        
        # Convert NumPy types for JSON serialization
        result = convert_numpy_types(result)
        result['timestamp'] = datetime.now().isoformat()
        
        return jsonify(result)

    except Exception as e:
        print(f"Analysis error: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/portfolio')
def portfolio():
    try:
        # Use Portfolio Agent via orchestrator
        portfolio_result = agent_orchestrator.mcp_server.route_request("portfolio", {
            'action': 'get_holdings'
        })
        
        if not portfolio_result.get('success'):
            flash('Portfolio data not available. Please check Kite API connection.', 'warning')
            return render_template('portfolio.html', holdings=[], positions=[])

        holdings_result = agent_orchestrator.mcp_server.route_request("portfolio", {
            'action': 'get_holdings'
        })
        positions_result = agent_orchestrator.mcp_server.route_request("portfolio", {
            'action': 'get_positions'
        })
        
        holdings = holdings_result.get('data', {}).get('holdings', []) if holdings_result.get('success') else []
        positions = positions_result.get('data', {}).get('positions', []) if positions_result.get('success') else []

        return render_template('portfolio.html', holdings=holdings, positions=positions)
    except Exception as e:
        flash(f'Error fetching portfolio: {str(e)}', 'error')
        return render_template('portfolio.html', holdings=[], positions=[])

@app.route('/recommendations')
def recommendations():
    """Display buy recommendations page"""
    return render_template('recommendations.html')

@app.route('/sector-analysis')
def sector_analysis():
    """Display sector-wise stock analysis page"""
    return render_template('sector_analysis.html')

@app.route('/api/recommendations', methods=['GET', 'POST'])
def get_recommendations():
    """API endpoint to get buy recommendations using Multi-Agent System"""
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
        
        # Use Multi-Agent Orchestrator for stock scanning
        result = agent_orchestrator.scan_stocks(
            symbols=symbols,
            min_score=min_score,
            max_results=max_results
        )
        
        if 'error' in result:
            return jsonify(result), 500
        
        # Convert NumPy types to Python native types for JSON serialization
        result = convert_numpy_types(result)
        result['scanned_at'] = datetime.now().isoformat()
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Recommendations error: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/sell-recommendations')
def sell_recommendations():
    try:
        # Use Portfolio Agent via orchestrator
        result = agent_orchestrator.mcp_server.route_request("portfolio", {
            'action': 'get_sell_recommendations'
        })
        
        if not result.get('success'):
            return jsonify({'error': result.get('error', 'Portfolio not available')}), 503

        return jsonify(result.get('data', {}))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sector-analysis')
def get_sector_analysis():
    """Get sector-wise stock analysis using Multi-Agent System"""
    try:
        # Define 5 stocks from 5 different sectors
        sector_stocks = {
            'Technology': ['TCS', 'INFY'],
            'Banking': ['HDFCBANK', 'ICICIBANK'],
            'Energy': ['RELIANCE', 'ONGC'],
            'FMCG': ['HINDUNILVR', 'ITC'],
            'Automobile': ['MARUTI', 'TATAMOTORS']
        }
        
        sectors_data = []
        
        for sector_name, symbols in sector_stocks.items():
            stocks_data = []
            
            for symbol in symbols:
                try:
                    # Use orchestrator to analyze stock
                    analysis = agent_orchestrator.analyze_stock(symbol)
                    
                    if 'error' not in analysis:
                        # Calculate ratings based on signals
                        technical = analysis.get('technical_analysis', {})
                        buying = analysis.get('buying_analysis', {})
                        fundamental = analysis.get('fundamental_analysis', {})
                        
                        # Count signals
                        signals = technical.get('signals', {})
                        buy_signals = sum(1 for s in signals.values() if s == 'BUY')
                        sell_signals = sum(1 for s in signals.values() if s == 'SELL')
                        hold_signals = sum(1 for s in signals.values() if s == 'HOLD')
                        total_signals = buy_signals + sell_signals + hold_signals
                        
                        # Calculate percentages
                        if total_signals > 0:
                            buy_percent = (buy_signals / total_signals) * 100
                            sell_percent = (sell_signals / total_signals) * 100
                            neutral_percent = (hold_signals / total_signals) * 100
                        else:
                            # Fallback to AI analysis
                            should_buy = buying.get('should_buy', False)
                            confidence = buying.get('confidence_level', 'Low')
                            
                            if should_buy:
                                buy_percent = 60 if confidence == 'High' else 50 if confidence == 'Medium' else 40
                                sell_percent = 20
                                neutral_percent = 100 - buy_percent - sell_percent
                            else:
                                sell_percent = 50
                                neutral_percent = 30
                                buy_percent = 20
                        
                        # Adjust based on overall sentiment
                        sentiment = technical.get('overall_sentiment', 'NEUTRAL')
                        if sentiment == 'BULLISH':
                            buy_percent = min(100, buy_percent + 15)
                            sell_percent = max(0, sell_percent - 10)
                        elif sentiment == 'BEARISH':
                            sell_percent = min(100, sell_percent + 15)
                            buy_percent = max(0, buy_percent - 10)
                        
                        # Normalize to 100%
                        total = buy_percent + sell_percent + neutral_percent
                        if total > 0:
                            buy_percent = (buy_percent / total) * 100
                            sell_percent = (sell_percent / total) * 100
                            neutral_percent = (neutral_percent / total) * 100
                        
                        stocks_data.append({
                            'symbol': symbol,
                            'company_name': fundamental.get('company_name', symbol),
                            'current_price': float(analysis.get('current_price', 0)),
                            'ratings': {
                                'buy': float(buy_percent),
                                'sell': float(sell_percent),
                                'neutral': float(neutral_percent)
                            },
                            'technical_score': float(technical.get('overall_sentiment') == 'BULLISH' and 70 or technical.get('overall_sentiment') == 'BEARISH' and 30 or 50),
                            'fundamental_score': float(fundamental.get('fundamental_score', {}).get('score', 50)),
                            'overall_sentiment': sentiment
                        })
                except Exception as e:
                    print(f"Error analyzing {symbol}: {e}")
                    continue
            
            if stocks_data:
                sectors_data.append({
                    'sector_name': sector_name,
                    'stocks': stocks_data
                })
        
        # Convert NumPy types
        sectors_data = convert_numpy_types(sectors_data)
        
        return jsonify({
            'sectors': sectors_data,
            'total_sectors': len(sectors_data),
            'analyzed_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Sector analysis error: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def api_status():
    # Get agent status from orchestrator
    agent_status = agent_orchestrator.get_agent_status()
    
    status = {
        'kite_connected': kite_handler.is_connected() if kite_handler else False,
        'portfolio_available': agent_orchestrator.portfolio_agent.is_connected() if agent_orchestrator.portfolio_agent else False,
        'mcp_server': agent_status.get('mcp_server'),
        'total_agents': agent_status.get('total_agents'),
        'agents': agent_status.get('agents'),
        'services': {
            'technical_analysis': True,
            'fundamental_analysis': True,
            'ai_analysis': agent_orchestrator.ai_agent.ai_analyzer.is_available(),
            'risk_management': True,
            'stock_search': True,
            'multi_agent_system': True
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
    # For local development only
    # Production uses gunicorn (see Procfile)
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=port)