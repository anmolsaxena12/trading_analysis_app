"""
Portfolio Management Agent - MCP Agent for portfolio operations
"""
from agents.base_agent import BaseAgent
from utils.portfolio_manager import PortfolioManager
from utils.kite_handler import KiteHandler
from typing import Dict, Any, Optional


class PortfolioAgent(BaseAgent):
    """Agent responsible for portfolio management"""
    
    def __init__(self, kite_handler: Optional[KiteHandler] = None):
        super().__init__("portfolio", "Portfolio Management Agent")
        self.kite_handler = kite_handler
        self.portfolio_manager = None
        
        if kite_handler and kite_handler.is_connected():
            self.portfolio_manager = PortfolioManager(kite_handler)
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process portfolio management request"""
        self.update_status("processing")
        
        try:
            if not self.portfolio_manager or not self.portfolio_manager.is_connected():
                return self.create_response(
                    False,
                    error="Portfolio manager not available. Kite API connection required."
                )
            
            action = context.get('action', 'get_holdings')
            
            if action == 'get_holdings':
                return self._get_holdings()
            elif action == 'get_positions':
                return self._get_positions()
            elif action == 'get_portfolio_analysis':
                return self._get_portfolio_analysis()
            elif action == 'get_sell_recommendations':
                return self._get_sell_recommendations()
            else:
                return self.create_response(False, error=f"Unknown action: {action}")
                
        except Exception as e:
            self.update_status("error")
            return self.create_response(False, error=str(e))
        finally:
            self.update_status("idle")
    
    def _get_holdings(self) -> Dict[str, Any]:
        """Get current holdings"""
        try:
            holdings = self.portfolio_manager.get_holdings()
            return self.create_response(True, data={'holdings': holdings})
        except Exception as e:
            return self.create_response(False, error=str(e))
    
    def _get_positions(self) -> Dict[str, Any]:
        """Get current positions"""
        try:
            positions = self.portfolio_manager.get_positions()
            return self.create_response(True, data={'positions': positions})
        except Exception as e:
            return self.create_response(False, error=str(e))
    
    def _get_portfolio_analysis(self) -> Dict[str, Any]:
        """Get portfolio analysis"""
        try:
            analysis = self.portfolio_manager.get_portfolio_analysis()
            return self.create_response(True, data=analysis)
        except Exception as e:
            return self.create_response(False, error=str(e))
    
    def _get_sell_recommendations(self) -> Dict[str, Any]:
        """Get sell recommendations"""
        try:
            recommendations = self.portfolio_manager.get_sell_recommendations()
            return self.create_response(True, data=recommendations)
        except Exception as e:
            return self.create_response(False, error=str(e))
    
    def is_connected(self) -> bool:
        """Check if portfolio is connected"""
        return self.portfolio_manager is not None and self.portfolio_manager.is_connected()

