"""
Agent Orchestrator — coordinates multiple agents using the MCP server.

Key improvements:
  - MCPServer is created first, then passed to AIAnalysisAgent so that
    AIAnalyzer can register tools with it (no more bypassing the agent layer)
  - Technical agent fetches its own OHLC data — direct FundamentalAnalyzer
    bypass in the old code is removed
  - Parallel stock scanning via ThreadPoolExecutor (5 workers)
  - Gradient technical score (signal-count ratio, not binary 70/50/30)
  - Structured logging throughout
  - Named bare-except replaced with logged Exception handler
"""
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeout
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from agents.mcp_server import MCPServer
from agents.stock_search_agent import StockSearchAgent
from agents.technical_agent import TechnicalAnalysisAgent
from agents.fundamental_agent import FundamentalAnalysisAgent
from agents.risk_agent import RiskManagementAgent
from agents.ai_agent import AIAnalysisAgent
from agents.portfolio_agent import PortfolioAgent
from utils.kite_handler import KiteHandler
from utils.logger import get_logger

logger = get_logger(__name__)

# Maximum parallel workers for the stock scan loop
_SCAN_WORKERS = 5
# Per-symbol analysis timeout (seconds)
_SYMBOL_TIMEOUT = 90


class AgentOrchestrator:
    """Orchestrates multiple agents for trading analysis."""

    def __init__(self, kite_handler: Optional[KiteHandler] = None):
        # Create the MCP server FIRST so agents can register tools with it
        self.mcp_server = MCPServer("trading_analysis_mcp")

        # Initialize all agents
        self.stock_search_agent = StockSearchAgent()
        self.technical_agent = TechnicalAnalysisAgent()
        self.fundamental_agent = FundamentalAnalysisAgent()
        self.risk_agent = RiskManagementAgent()
        # Pass MCPServer so AIAnalyzer registers tools (get_technical_signals, etc.)
        self.ai_agent = AIAnalysisAgent(mcp_server=self.mcp_server)
        self.portfolio_agent = PortfolioAgent(kite_handler)

        # Register agents with MCP server
        self.mcp_server.register_agent("stock_search", self.stock_search_agent)
        self.mcp_server.register_agent("technical_analysis", self.technical_agent)
        self.mcp_server.register_agent("fundamental_analysis", self.fundamental_agent)
        self.mcp_server.register_agent("risk_management", self.risk_agent)
        self.mcp_server.register_agent("ai_analysis", self.ai_agent)
        self.mcp_server.register_agent("portfolio", self.portfolio_agent)

        tools_registered = len(self.mcp_server.tools)
        logger.info(
            "AgentOrchestrator ready — %d agents, %d tools registered with MCP server.",
            len(self.mcp_server.agents),
            tools_registered,
        )

    # ------------------------------------------------------------------
    # Single-stock analysis pipeline
    # ------------------------------------------------------------------

    def analyze_stock(self, symbol: str) -> Dict[str, Any]:
        """Orchestrate full stock analysis using all agents in sequence."""
        try:
            symbol = symbol.upper().strip()
            logger.info("[%s] Starting analysis pipeline.", symbol)

            # Step 1 — Validate symbol and get current price
            search_result = self.mcp_server.route_request("stock_search", {
                "action": "search",
                "symbol": symbol,
            })
            if not search_result.get("success"):
                return {"error": search_result.get("error", "Stock search failed")}

            symbol_data = search_result["data"]
            current_price = symbol_data["current_price"]

            # Step 2 — Technical analysis
            # TechnicalAnalysisAgent fetches its own OHLC data when stock_data is None
            technical_result = self.mcp_server.route_request("technical_analysis", {
                "symbol": symbol,
            })
            if not technical_result.get("success"):
                return {"error": technical_result.get("error", "Technical analysis failed")}
            technical_signals = technical_result["data"]

            # Step 3 — Fundamental analysis
            fundamental_result = self.mcp_server.route_request("fundamental_analysis", {
                "symbol": symbol,
            })
            if not fundamental_result.get("success"):
                return {"error": fundamental_result.get("error", "Fundamental analysis failed")}
            fundamental_data = fundamental_result["data"]

            # Step 4 — AI analysis (runs agentic loop if tools are registered)
            ai_result = self.mcp_server.route_request("ai_analysis", {
                "symbol": symbol,
                "current_price": current_price,
                "technical_signals": technical_signals,
                "fundamental_data": fundamental_data,
            })
            if not ai_result.get("success"):
                return {"error": ai_result.get("error", "AI analysis failed")}
            buying_analysis = ai_result["data"]

            # Step 5 — Risk-reward (only when AI recommends buying)
            risk_reward = None
            if buying_analysis.get("should_buy", False):
                risk_result = self.mcp_server.route_request("risk_management", {
                    "action": "calculate_risk_reward",
                    "entry_price": current_price,
                    "target_price": buying_analysis.get("target_price", current_price * 1.1),
                    "stop_loss": buying_analysis.get("stop_loss", current_price * 0.95),
                })
                if risk_result.get("success"):
                    risk_reward = risk_result["data"]

            logger.info("[%s] Analysis pipeline complete.", symbol)
            return {
                "symbol": symbol,
                "current_price": current_price,
                "technical_analysis": technical_signals,
                "fundamental_analysis": fundamental_data,
                "buying_analysis": buying_analysis,
                "risk_reward": risk_reward,
                "agents_used": [
                    "stock_search",
                    "technical_analysis",
                    "fundamental_analysis",
                    "ai_analysis",
                    "risk_management",
                ],
            }

        except Exception as e:
            logger.error("[%s] Orchestration error: %s", symbol, e, exc_info=True)
            return {"error": str(e)}

    # ------------------------------------------------------------------
    # Parallel stock scan
    # ------------------------------------------------------------------

    def scan_stocks(
        self,
        symbols: Optional[List[str]] = None,
        min_score: int = 60,
        max_results: int = 20,
    ) -> Dict[str, Any]:
        """
        Scan multiple stocks in parallel and return top recommendations.
        Uses ThreadPoolExecutor with up to _SCAN_WORKERS concurrent workers.
        """
        try:
            if symbols is None:
                symbols = self.stock_search_agent.default_stocks

            # Validate available symbols via stock search agent
            scan_result = self.mcp_server.route_request("stock_search", {
                "action": "scan",
                "symbols": symbols,
                "max_results": max_results,
            })
            if not scan_result.get("success"):
                return {"error": scan_result.get("error", "Stock scan failed")}

            available_stocks = scan_result["data"]["stocks"]
            target_symbols = [s["symbol"] for s in available_stocks[:max_results]]

            logger.info(
                "Scanning %d stocks with %d parallel workers.",
                len(target_symbols), _SCAN_WORKERS
            )

            recommendations: List[Dict[str, Any]] = []

            with ThreadPoolExecutor(max_workers=_SCAN_WORKERS) as executor:
                future_to_symbol = {
                    executor.submit(self.analyze_stock, sym): sym
                    for sym in target_symbols
                }
                for future in as_completed(future_to_symbol):
                    sym = future_to_symbol[future]
                    try:
                        analysis = future.result(timeout=_SYMBOL_TIMEOUT)
                    except FutureTimeout:
                        logger.warning("[%s] Analysis timed out after %ds — skipping.", sym, _SYMBOL_TIMEOUT)
                        continue
                    except Exception as e:
                        logger.error("[%s] Analysis raised exception: %s — skipping.", sym, e)
                        continue

                    if "error" in analysis:
                        logger.warning("[%s] Analysis error: %s — skipping.", sym, analysis["error"])
                        continue

                    overall_score = self._calculate_overall_score(analysis)
                    if overall_score < min_score:
                        continue

                    rec = self._build_recommendation(analysis, overall_score)
                    if rec:
                        recommendations.append(rec)

            recommendations.sort(key=lambda x: x["overall_score"], reverse=True)
            logger.info(
                "Scan complete — %d/%d stocks met min_score=%d.",
                len(recommendations), len(target_symbols), min_score
            )

            return {
                "recommendations": recommendations[:max_results],
                "count": len(recommendations),
                "agents_used": [
                    "stock_search",
                    "technical_analysis",
                    "fundamental_analysis",
                    "ai_analysis",
                    "risk_management",
                ],
            }

        except Exception as e:
            logger.error("Scan orchestration error: %s", e, exc_info=True)
            return {"error": str(e)}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _calculate_overall_score(self, analysis: Dict[str, Any]) -> float:
        """
        Weighted overall score:
          - Technical (40%): gradient from signal count ratio, not binary buckets
          - Fundamental (30%): fundamental_score from FundamentalAnalyzer
          - AI (30%): overall_score from Gemini / fallback
        """
        try:
            technical = analysis.get("technical_analysis", {})
            fundamental = analysis.get("fundamental_analysis", {})
            buying = analysis.get("buying_analysis", {})

            # Gradient technical score: (+/-)30 points from signal ratio
            signals = technical.get("signals", {})
            buy_count = sum(1 for v in signals.values() if v == "BUY")
            sell_count = sum(1 for v in signals.values() if v == "SELL")
            total_sigs = len(signals) or 1
            tech_score = 50.0 + ((buy_count - sell_count) / total_sigs) * 30.0
            tech_score = max(0.0, min(100.0, tech_score))

            fund_score = float(fundamental.get("fundamental_score", {}).get("score", 50))
            ai_score = float(buying.get("overall_score", 50))

            return (tech_score * 0.4) + (fund_score * 0.3) + (ai_score * 0.3)

        except Exception as e:
            logger.error("Score calculation failed: %s", e)
            return 50.0

    def _build_recommendation(self, analysis: Dict[str, Any], overall_score: float) -> Optional[Dict[str, Any]]:
        """Format a scan result into a recommendation dict."""
        try:
            symbol = analysis["symbol"]
            current_price = float(analysis.get("current_price", 0))
            buying_analysis = analysis.get("buying_analysis", {})
            risk_reward = analysis.get("risk_reward")
            fundamental = analysis.get("fundamental_analysis", {})
            technical = analysis.get("technical_analysis", {})

            target_price = float(buying_analysis.get("target_price", current_price * 1.1))
            stop_loss = float(buying_analysis.get("stop_loss", current_price * 0.95))

            buy_date = datetime.now()
            sell_date = buy_date + timedelta(days=21)

            return {
                "symbol": symbol,
                "company_name": fundamental.get("company_name", symbol),
                "current_price": current_price,
                "buy_price": current_price,
                "target_price": target_price,
                "stop_loss": stop_loss,
                "risk_reward": risk_reward or {
                    "entry_price": current_price,
                    "target_price": target_price,
                    "stop_loss_price": stop_loss,
                    "risk_reward_ratio": 2.0,
                    "ratio_formatted": "1:2.00",
                    "is_favorable": True,
                },
                "overall_score": float(overall_score),
                "technical_score": float(
                    50.0 + (
                        sum(1 for v in technical.get("signals", {}).values() if v == "BUY") -
                        sum(1 for v in technical.get("signals", {}).values() if v == "SELL")
                    ) / max(len(technical.get("signals", {})), 1) * 30.0
                ),
                "fundamental_score": float(
                    fundamental.get("fundamental_score", {}).get("score", 50)
                ),
                "ai_score": float(buying_analysis.get("overall_score", 50)),
                "confidence": buying_analysis.get("confidence_level", "Medium"),
                "timeline": {
                    "buy_date": buy_date.strftime("%Y-%m-%d"),
                    "expected_sell_date": sell_date.strftime("%Y-%m-%d"),
                    "days_holding": 21,
                    "time_horizon": buying_analysis.get("time_horizon", "Medium term"),
                },
                "key_reasons": buying_analysis.get("key_reasons", [])[:3],
                "risks": buying_analysis.get("risks", [])[:2],
                "sector": fundamental.get("sector_info", {}).get("sector", "Unknown"),
                "technical_signals": {
                    "rsi": technical.get("rsi"),
                    "macd_signal": technical.get("signals", {}).get("macd_signal"),
                    "trend_signal": technical.get("signals", {}).get("trend_signal"),
                    "overall_sentiment": technical.get("overall_sentiment"),
                },
                "potential_profit_percent": float(
                    ((target_price - current_price) / current_price) * 100
                ) if current_price else 0.0,
                "risk_percent": float(
                    ((current_price - stop_loss) / current_price) * 100
                ) if current_price else 0.0,
                "scanned_at": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error("Failed to build recommendation for %s: %s", analysis.get("symbol"), e)
            return None

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def get_agent_status(self) -> Dict[str, Any]:
        """Return status of all registered agents and the MCP server."""
        return {
            "mcp_server": self.mcp_server.server_name,
            "agents": self.mcp_server.get_available_agents(),
            "total_agents": len(self.mcp_server.agents),
            "tools_registered": len(self.mcp_server.tools),
            "tool_names": list(self.mcp_server.tools.keys()),
        }
