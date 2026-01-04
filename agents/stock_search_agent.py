"""
Stock Search Agent - MCP Agent for searching and scanning stocks
"""
from agents.base_agent import BaseAgent
from utils.fundamental_analyzer import FundamentalAnalyzer
from typing import Dict, Any, List


class StockSearchAgent(BaseAgent):
    """Agent responsible for searching and scanning stocks"""
    
    def __init__(self):
        super().__init__("stock_search", "Stock Search Agent")
        self.fundamental_analyzer = FundamentalAnalyzer()
        self.default_stocks = [
            'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR', 'ICICIBANK',
            'BHARTIARTL', 'SBIN', 'BAJFINANCE', 'LICI', 'ITC', 'SUNPHARMA',
            'HCLTECH', 'AXISBANK', 'KOTAKBANK', 'LT', 'ASIANPAINT', 'MARUTI',
            'TITAN', 'ULTRACEMCO', 'NESTLEIND', 'WIPRO', 'ONGC', 'NTPC',
            'POWERGRID', 'TECHM', 'ADANIENT', 'JSWSTEEL', 'TATAMOTORS', 'TATASTEEL'
        ]
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process stock search/scan request"""
        self.update_status("processing")
        
        try:
            action = context.get('action', 'search')
            
            if action == 'search':
                return self._search_stock(context)
            elif action == 'scan':
                return self._scan_stocks(context)
            elif action == 'validate':
                return self._validate_symbol(context)
            else:
                return self.create_response(
                    False,
                    error=f"Unknown action: {action}"
                )
        except Exception as e:
            self.update_status("error")
            return self.create_response(False, error=str(e))
        finally:
            self.update_status("idle")
    
    def _search_stock(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Search for a specific stock"""
        symbol = context.get('symbol', '').upper()
        
        if not symbol:
            return self.create_response(False, error="Symbol is required")
        
        # Try to fetch stock data to validate
        stock_data = self.fundamental_analyzer.get_stock_data(symbol)
        
        if stock_data.empty:
            return self.create_response(
                False,
                error=f"Stock {symbol} not found or data unavailable"
            )
        
        current_price = float(stock_data['Close'].iloc[-1])
        
        return self.create_response(True, data={
            'symbol': symbol,
            'current_price': current_price,
            'data_available': True,
            'data_points': len(stock_data)
        })
    
    def _scan_stocks(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Scan multiple stocks"""
        symbols = context.get('symbols', self.default_stocks)
        max_results = context.get('max_results', 20)
        
        available_stocks = []
        
        for symbol in symbols[:max_results]:
            stock_data = self.fundamental_analyzer.get_stock_data(symbol)
            if not stock_data.empty:
                available_stocks.append({
                    'symbol': symbol,
                    'data_available': True,
                    'data_points': len(stock_data)
                })
        
        return self.create_response(True, data={
            'scanned_count': len(available_stocks),
            'stocks': available_stocks
        })
    
    def _validate_symbol(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate if a stock symbol exists"""
        symbol = context.get('symbol', '').upper()
        
        if not symbol:
            return self.create_response(False, error="Symbol is required")
        
        stock_data = self.fundamental_analyzer.get_stock_data(symbol)
        is_valid = not stock_data.empty
        
        return self.create_response(True, data={
            'symbol': symbol,
            'valid': is_valid
        })

