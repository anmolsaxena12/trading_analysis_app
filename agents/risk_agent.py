"""
Risk Management Agent — MCP agent for risk calculations and position sizing.
"""
from agents.base_agent import BaseAgent
from utils.risk_manager import RiskManager
from utils.logger import get_logger
from typing import Any, Dict

logger = get_logger(__name__)


class RiskManagementAgent(BaseAgent):
    """Agent responsible for risk management calculations."""

    def __init__(self):
        super().__init__("risk_management", "Risk Management Agent")
        self.risk_manager = RiskManager()

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process risk management request — follows base agent status contract."""
        self.update_status("processing")

        try:
            action = context.get("action", "calculate_risk_reward")

            if action == "calculate_risk_reward":
                result = self._calculate_risk_reward(context)
            elif action == "calculate_position_size":
                result = self._calculate_position_size(context)
            elif action == "analyze_portfolio_risk":
                result = self._analyze_portfolio_risk(context)
            else:
                self.update_status("error")
                return self.create_response(False, error=f"Unknown action: {action}")

            if result.get("success") is False:
                self.update_status("error")
                return result

            self.update_status("idle")
            return result

        except Exception as e:
            logger.error("[risk_management] process failed: %s", e)
            self.update_status("error")
            return self.create_response(False, error=str(e))

    def _calculate_risk_reward(self, context: Dict[str, Any]) -> Dict[str, Any]:
        entry_price = context.get("entry_price")
        target_price = context.get("target_price")
        stop_loss = context.get("stop_loss")

        if not all([entry_price, target_price, stop_loss]):
            return self.create_response(
                False, error="entry_price, target_price, and stop_loss are required"
            )
        try:
            rr = self.risk_manager.calculate_risk_reward(
                float(entry_price), float(target_price), float(stop_loss)
            )
            if rr is None:
                return self.create_response(False, error="Could not calculate risk-reward")
            return self.create_response(True, data=rr)
        except Exception as e:
            return self.create_response(False, error=str(e))

    def _calculate_position_size(self, context: Dict[str, Any]) -> Dict[str, Any]:
        available_capital = context.get("available_capital")
        entry_price = context.get("entry_price")
        risk_reward_data = context.get("risk_reward_data")

        if not all([available_capital, entry_price, risk_reward_data]):
            return self.create_response(
                False, error="available_capital, entry_price, and risk_reward_data are required"
            )
        try:
            ps = self.risk_manager.calculate_position_size(
                float(available_capital), float(entry_price), risk_reward_data
            )
            if ps is None:
                return self.create_response(False, error="Could not calculate position size")
            return self.create_response(True, data=ps)
        except Exception as e:
            return self.create_response(False, error=str(e))

    def _analyze_portfolio_risk(self, context: Dict[str, Any]) -> Dict[str, Any]:
        positions = context.get("positions", [])
        current_prices = context.get("current_prices", {})

        if not positions:
            return self.create_response(False, error="positions list is required")
        try:
            pr = self.risk_manager.analyze_portfolio_risk(positions, current_prices)
            if pr is None:
                return self.create_response(False, error="Could not analyze portfolio risk")
            return self.create_response(True, data=pr)
        except Exception as e:
            return self.create_response(False, error=str(e))
