"""
Technical Analysis Agent — MCP agent for technical indicators and signals.
"""
from agents.base_agent import BaseAgent
from utils.technical_analyzer import TechnicalAnalyzer
from utils.fundamental_analyzer import FundamentalAnalyzer
from utils.logger import get_logger
from typing import Any, Dict

logger = get_logger(__name__)


class TechnicalAnalysisAgent(BaseAgent):
    """Agent responsible for technical analysis."""

    def __init__(self):
        super().__init__("technical_analysis", "Technical Analysis Agent")
        self.technical_analyzer = TechnicalAnalyzer()
        self.fundamental_analyzer = FundamentalAnalyzer()

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process technical analysis request — follows base agent status contract."""
        self.update_status("processing")

        try:
            symbol = context.get("symbol", "").upper()
            stock_data = context.get("stock_data")

            if not symbol and stock_data is None:
                self.update_status("error")
                return self.create_response(False, error="symbol or stock_data is required")

            if stock_data is None:
                stock_data = self.fundamental_analyzer.get_stock_data(symbol)
                if stock_data.empty:
                    self.update_status("error")
                    return self.create_response(False, error=f"Could not fetch data for {symbol}")

            analysis = self.technical_analyzer.analyze(stock_data)

            if analysis.get("error"):
                self.update_status("error")
                return self.create_response(False, error=analysis["error"])

            self.update_status("idle")
            return self.create_response(True, data=analysis)

        except Exception as e:
            logger.error("[technical_analysis] process failed: %s", e)
            self.update_status("error")
            return self.create_response(False, error=str(e))

    def calculate_indicator(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate a specific technical indicator by name."""
        indicator = context.get("indicator")
        stock_data = context.get("stock_data")

        if not indicator or stock_data is None:
            return self.create_response(False, error="indicator and stock_data are required")

        try:
            if indicator == "rsi":
                rsi = self.technical_analyzer.calculate_rsi(stock_data)
                return self.create_response(True, data={"rsi": float(rsi[-1]) if len(rsi) > 0 else None})
            elif indicator == "macd":
                macd, signal, hist = self.technical_analyzer.calculate_macd(stock_data)
                return self.create_response(True, data={
                    "macd": float(macd[-1]) if len(macd) > 0 else None,
                    "signal": float(signal[-1]) if len(signal) > 0 else None,
                    "histogram": float(hist[-1]) if len(hist) > 0 else None,
                })
            else:
                return self.create_response(False, error=f"Unknown indicator: {indicator}")
        except Exception as e:
            return self.create_response(False, error=str(e))
