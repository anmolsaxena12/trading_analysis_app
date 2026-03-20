"""
Fundamental Analysis Agent — MCP agent for fundamental analysis.
"""
from agents.base_agent import BaseAgent
from utils.fundamental_analyzer import FundamentalAnalyzer
from utils.logger import get_logger
from typing import Any, Dict

logger = get_logger(__name__)


class FundamentalAnalysisAgent(BaseAgent):
    """Agent responsible for fundamental analysis."""

    def __init__(self):
        super().__init__("fundamental_analysis", "Fundamental Analysis Agent")
        self.fundamental_analyzer = FundamentalAnalyzer()

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process fundamental analysis request — follows base agent status contract.

        Supported actions (via context['action']):
          - 'analyze' (default) : full fundamental analysis
          - 'get_stock_data'    : return OHLC price data
        """
        self.update_status("processing")

        try:
            action = context.get("action", "analyze")
            symbol = context.get("symbol", "").upper()

            if not symbol:
                self.update_status("error")
                return self.create_response(False, error="symbol is required")

            if action == "get_stock_data":
                result = self._get_stock_data(symbol, context.get("period", "1y"))
            else:
                result = self._analyze(symbol)

            if result.get("success") is False:
                self.update_status("error")
                return result

            self.update_status("idle")
            return result

        except Exception as e:
            logger.error("[fundamental_analysis] process failed: %s", e)
            self.update_status("error")
            return self.create_response(False, error=str(e))

    def _analyze(self, symbol: str) -> Dict[str, Any]:
        analysis = self.fundamental_analyzer.analyze(symbol)
        if analysis.get("error"):
            return self.create_response(False, error=analysis["error"])
        return self.create_response(True, data=analysis)

    def _get_stock_data(self, symbol: str, period: str) -> Dict[str, Any]:
        stock_data = self.fundamental_analyzer.get_stock_data(symbol, period)
        if stock_data.empty:
            return self.create_response(False, error=f"Could not fetch data for {symbol}")
        return self.create_response(True, data={
            "symbol": symbol,
            "period": period,
            "rows": len(stock_data),
            "current_price": float(stock_data["Close"].iloc[-1]),
            "dates": stock_data.index.strftime("%Y-%m-%d").tolist()[-10:],
            "prices": stock_data["Close"].tail(10).tolist(),
        })

    def get_financial_ratios(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get financial ratios for a stock."""
        symbol = context.get("symbol", "").upper()
        if not symbol:
            return self.create_response(False, error="symbol is required")
        try:
            info = self.fundamental_analyzer.get_company_info(symbol)
            ratios = self.fundamental_analyzer.calculate_financial_ratios(info)
            return self.create_response(True, data=ratios)
        except Exception as e:
            return self.create_response(False, error=str(e))
