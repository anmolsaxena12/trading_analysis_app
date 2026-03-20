"""
Stock Search Agent — MCP agent for searching and scanning NSE/BSE stocks.
"""
import re
from agents.base_agent import BaseAgent
from utils.fundamental_analyzer import FundamentalAnalyzer
from utils.logger import get_logger
from typing import Any, Dict, List

logger = get_logger(__name__)

# Regex that matches valid NSE/BSE stock symbols
_SYMBOL_RE = re.compile(r'^[A-Z0-9&.\-]{1,20}$')


class StockSearchAgent(BaseAgent):
    """Agent responsible for searching and scanning stocks."""

    def __init__(self):
        super().__init__("stock_search", "Stock Search Agent")
        self.fundamental_analyzer = FundamentalAnalyzer()
        self.default_stocks: List[str] = [
            "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR", "ICICIBANK",
            "BHARTIARTL", "SBIN", "BAJFINANCE", "LICI", "ITC", "SUNPHARMA",
            "HCLTECH", "AXISBANK", "KOTAKBANK", "LT", "ASIANPAINT", "MARUTI",
            "TITAN", "ULTRACEMCO", "NESTLEIND", "WIPRO", "ONGC", "NTPC",
            "POWERGRID", "TECHM", "ADANIENT", "JSWSTEEL", "TATAMOTORS", "TATASTEEL",
        ]

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process stock search/scan request — follows base agent status contract."""
        self.update_status("processing")

        try:
            action = context.get("action", "search")

            if action == "search":
                result = self._search_stock(context)
            elif action == "scan":
                result = self._scan_stocks(context)
            elif action == "validate":
                result = self._validate_symbol(context)
            else:
                self.update_status("error")
                return self.create_response(False, error=f"Unknown action: {action}")

            if result.get("success") is False:
                self.update_status("error")
                return result

            self.update_status("idle")
            return result

        except Exception as e:
            logger.error("[stock_search] process failed: %s", e)
            self.update_status("error")
            return self.create_response(False, error=str(e))

    def _validate_symbol_format(self, symbol: str) -> bool:
        """Validate symbol format to prevent injection attacks."""
        return bool(_SYMBOL_RE.match(symbol))

    def _search_stock(self, context: Dict[str, Any]) -> Dict[str, Any]:
        symbol = context.get("symbol", "").upper().strip()

        if not symbol:
            return self.create_response(False, error="symbol is required")

        if not self._validate_symbol_format(symbol):
            return self.create_response(
                False, error=f"Invalid symbol format: '{symbol}'. Expected 1-20 uppercase alphanumeric characters."
            )

        stock_data = self.fundamental_analyzer.get_stock_data(symbol)
        if stock_data.empty:
            return self.create_response(False, error=f"Stock '{symbol}' not found or data unavailable")

        return self.create_response(True, data={
            "symbol": symbol,
            "current_price": float(stock_data["Close"].iloc[-1]),
            "data_available": True,
            "data_points": len(stock_data),
        })

    def _scan_stocks(self, context: Dict[str, Any]) -> Dict[str, Any]:
        symbols: List[str] = context.get("symbols", self.default_stocks)
        max_results: int = context.get("max_results", 20)

        available = []
        for symbol in symbols[:max_results]:
            symbol = symbol.upper().strip()
            if not self._validate_symbol_format(symbol):
                logger.warning("[stock_search] Skipping invalid symbol: %s", symbol)
                continue
            stock_data = self.fundamental_analyzer.get_stock_data(symbol)
            if not stock_data.empty:
                available.append({
                    "symbol": symbol,
                    "data_available": True,
                    "data_points": len(stock_data),
                })

        return self.create_response(True, data={
            "scanned_count": len(available),
            "stocks": available,
        })

    def _validate_symbol(self, context: Dict[str, Any]) -> Dict[str, Any]:
        symbol = context.get("symbol", "").upper().strip()
        if not symbol:
            return self.create_response(False, error="symbol is required")
        if not self._validate_symbol_format(symbol):
            return self.create_response(True, data={"symbol": symbol, "valid": False, "reason": "Invalid format"})

        stock_data = self.fundamental_analyzer.get_stock_data(symbol)
        return self.create_response(True, data={
            "symbol": symbol,
            "valid": not stock_data.empty,
        })
