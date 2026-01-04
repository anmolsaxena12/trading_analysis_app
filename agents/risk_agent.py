"""
Risk Management Agent - MCP Agent for risk calculations and position sizing
"""
from agents.base_agent import BaseAgent
from utils.risk_manager import RiskManager
from typing import Dict, Any


class RiskManagementAgent(BaseAgent):
    """Agent responsible for risk management calculations"""
    
    def __init__(self):
        super().__init__("risk_management", "Risk Management Agent")
        self.risk_manager = RiskManager()
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process risk management request"""
        self.update_status("processing")
        
        try:
            action = context.get('action', 'calculate_risk_reward')
            
            if action == 'calculate_risk_reward':
                return self._calculate_risk_reward(context)
            elif action == 'calculate_position_size':
                return self._calculate_position_size(context)
            elif action == 'analyze_portfolio_risk':
                return self._analyze_portfolio_risk(context)
            else:
                return self.create_response(False, error=f"Unknown action: {action}")
                
        except Exception as e:
            self.update_status("error")
            return self.create_response(False, error=str(e))
        finally:
            self.update_status("idle")
    
    def _calculate_risk_reward(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate risk-reward ratio"""
        entry_price = context.get('entry_price')
        target_price = context.get('target_price')
        stop_loss = context.get('stop_loss')
        
        if not all([entry_price, target_price, stop_loss]):
            return self.create_response(False, error="entry_price, target_price, and stop_loss required")
        
        try:
            risk_reward = self.risk_manager.calculate_risk_reward(
                float(entry_price),
                float(target_price),
                float(stop_loss)
            )
            
            if risk_reward is None:
                return self.create_response(False, error="Could not calculate risk-reward")
            
            return self.create_response(True, data=risk_reward)
        except Exception as e:
            return self.create_response(False, error=str(e))
    
    def _calculate_position_size(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate position size"""
        available_capital = context.get('available_capital')
        entry_price = context.get('entry_price')
        risk_reward_data = context.get('risk_reward_data')
        
        if not all([available_capital, entry_price, risk_reward_data]):
            return self.create_response(False, error="available_capital, entry_price, and risk_reward_data required")
        
        try:
            position_size = self.risk_manager.calculate_position_size(
                float(available_capital),
                float(entry_price),
                risk_reward_data
            )
            
            if position_size is None:
                return self.create_response(False, error="Could not calculate position size")
            
            return self.create_response(True, data=position_size)
        except Exception as e:
            return self.create_response(False, error=str(e))
    
    def _analyze_portfolio_risk(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze portfolio risk"""
        positions = context.get('positions', [])
        current_prices = context.get('current_prices', {})
        
        if not positions:
            return self.create_response(False, error="positions required")
        
        try:
            portfolio_risk = self.risk_manager.analyze_portfolio_risk(positions, current_prices)
            
            if portfolio_risk is None:
                return self.create_response(False, error="Could not analyze portfolio risk")
            
            return self.create_response(True, data=portfolio_risk)
        except Exception as e:
            return self.create_response(False, error=str(e))

