"""
Technical Analysis Agent - MCP Agent for technical indicators and signals
"""
from agents.base_agent import BaseAgent
from utils.technical_analyzer import TechnicalAnalyzer
from utils.fundamental_analyzer import FundamentalAnalyzer
from typing import Dict, Any


class TechnicalAnalysisAgent(BaseAgent):
    """Agent responsible for technical analysis"""
    
    def __init__(self):
        super().__init__("technical_analysis", "Technical Analysis Agent")
        self.technical_analyzer = TechnicalAnalyzer()
        self.fundamental_analyzer = FundamentalAnalyzer()
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process technical analysis request"""
        self.update_status("processing")
        
        try:
            symbol = context.get('symbol', '').upper()
            stock_data = context.get('stock_data')
            
            if not symbol and stock_data is None:
                return self.create_response(False, error="Symbol or stock_data required")
            
            # Get stock data if not provided
            if stock_data is None:
                stock_data = self.fundamental_analyzer.get_stock_data(symbol)
                if stock_data.empty:
                    return self.create_response(False, error=f"Could not fetch data for {symbol}")
            
            # Perform technical analysis
            analysis = self.technical_analyzer.analyze(stock_data)
            
            if analysis.get('error'):
                return self.create_response(False, error=analysis.get('error'))
            
            return self.create_response(True, data=analysis)
            
        except Exception as e:
            self.update_status("error")
            return self.create_response(False, error=str(e))
        finally:
            self.update_status("idle")
    
    def calculate_indicator(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate a specific technical indicator"""
        indicator = context.get('indicator')
        stock_data = context.get('stock_data')
        
        if not indicator or stock_data is None:
            return self.create_response(False, error="Indicator and stock_data required")
        
        try:
            if indicator == 'rsi':
                rsi = self.technical_analyzer.calculate_rsi(stock_data)
                return self.create_response(True, data={'rsi': float(rsi[-1]) if len(rsi) > 0 else None})
            elif indicator == 'macd':
                macd, signal, hist = self.technical_analyzer.calculate_macd(stock_data)
                return self.create_response(True, data={
                    'macd': float(macd[-1]) if len(macd) > 0 else None,
                    'signal': float(signal[-1]) if len(signal) > 0 else None,
                    'histogram': float(hist[-1]) if len(hist) > 0 else None
                })
            else:
                return self.create_response(False, error=f"Unknown indicator: {indicator}")
        except Exception as e:
            return self.create_response(False, error=str(e))

