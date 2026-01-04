"""
Fundamental Analysis Agent - MCP Agent for fundamental analysis
"""
from agents.base_agent import BaseAgent
from utils.fundamental_analyzer import FundamentalAnalyzer
from typing import Dict, Any


class FundamentalAnalysisAgent(BaseAgent):
    """Agent responsible for fundamental analysis"""
    
    def __init__(self):
        super().__init__("fundamental_analysis", "Fundamental Analysis Agent")
        self.fundamental_analyzer = FundamentalAnalyzer()
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process fundamental analysis request"""
        self.update_status("processing")
        
        try:
            symbol = context.get('symbol', '').upper()
            
            if not symbol:
                return self.create_response(False, error="Symbol is required")
            
            # Perform fundamental analysis
            analysis = self.fundamental_analyzer.analyze(symbol)
            
            if analysis.get('error'):
                return self.create_response(False, error=analysis.get('error'))
            
            return self.create_response(True, data=analysis)
            
        except Exception as e:
            self.update_status("error")
            return self.create_response(False, error=str(e))
        finally:
            self.update_status("idle")
    
    def get_financial_ratios(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get financial ratios for a stock"""
        symbol = context.get('symbol', '').upper()
        
        if not symbol:
            return self.create_response(False, error="Symbol is required")
        
        try:
            info = self.fundamental_analyzer.get_company_info(symbol)
            ratios = self.fundamental_analyzer.calculate_financial_ratios(info)
            
            return self.create_response(True, data=ratios)
        except Exception as e:
            return self.create_response(False, error=str(e))
    
    def get_stock_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get stock price data"""
        symbol = context.get('symbol', '').upper()
        period = context.get('period', '1y')
        
        if not symbol:
            return self.create_response(False, error="Symbol is required")
        
        try:
            stock_data = self.fundamental_analyzer.get_stock_data(symbol, period)
            
            if stock_data.empty:
                return self.create_response(False, error=f"Could not fetch data for {symbol}")
            
            # Convert to dict for JSON serialization
            data_dict = {
                'symbol': symbol,
                'period': period,
                'rows': len(stock_data),
                'current_price': float(stock_data['Close'].iloc[-1]),
                'dates': stock_data.index.strftime('%Y-%m-%d').tolist()[-10:],  # Last 10 dates
                'prices': stock_data['Close'].tail(10).tolist()
            }
            
            return self.create_response(True, data=data_dict)
        except Exception as e:
            return self.create_response(False, error=str(e))

