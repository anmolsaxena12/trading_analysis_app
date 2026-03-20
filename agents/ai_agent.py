"""
AI Analysis Agent — MCP agent for Gemini-powered recommendations.

Passes the MCPServer reference to AIAnalyzer so that Gemini can call
registered tools (get_technical_signals, get_fundamental_data,
calculate_risk_reward) autonomously during the agentic loop.
"""
from agents.base_agent import BaseAgent
from utils.ai_analyzer import AIAnalyzer
from utils.logger import get_logger
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from agents.mcp_server import MCPServer

logger = get_logger(__name__)


class AIAnalysisAgent(BaseAgent):
    """Agent responsible for AI-powered analysis and recommendations."""

    def __init__(self, mcp_server: Optional["MCPServer"] = None):
        super().__init__("ai_analysis", "AI Analysis Agent")
        # Pass MCPServer so AIAnalyzer can register tools and run the agentic loop
        self.ai_analyzer = AIAnalyzer(mcp_server=mcp_server)

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process AI analysis request — follows base agent status contract."""
        self.update_status("processing")

        symbol = context.get("symbol")
        current_price = context.get("current_price")
        technical_signals = context.get("technical_signals")
        fundamental_data = context.get("fundamental_data")

        if not all([symbol, current_price, technical_signals is not None, fundamental_data is not None]):
            self.update_status("error")
            return self.create_response(
                False,
                error="symbol, current_price, technical_signals, and fundamental_data are required"
            )

        try:
            analysis = self.ai_analyzer.analyze_buying_opportunity(
                symbol,
                float(current_price),
                technical_signals,
                fundamental_data,
            )
            self.update_status("idle")
            return self.create_response(True, data=analysis)

        except Exception as e:
            logger.error("[ai_analysis] process failed for %s: %s", symbol, e)
            self.update_status("error")
            return self.create_response(False, error=str(e))

    def get_ai_status(self) -> Dict[str, Any]:
        """Return AI availability and agent status."""
        return self.create_response(True, data={
            "ai_available": self.ai_analyzer.is_available(),
            "agent_status": self.get_status(),
        })
