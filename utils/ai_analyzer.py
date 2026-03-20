"""
AI Analyzer — Gemini-powered stock analysis with a true agentic loop.

Uses the new google-genai SDK (google.genai ≥ 1.0.0).

Architecture:
  1. Gemini is given a system instruction (analyst persona) + tool declarations.
  2. On each request Gemini may call tools (get_technical_signals,
     get_fundamental_data, calculate_risk_reward) to fetch data it needs.
  3. We execute each tool call through the MCPServer and feed results back
     via FunctionResponse parts.
  4. Gemini produces a final JSON response validated by Pydantic.

Key improvements over the original:
  - System instruction sets analyst persona and enforces JSON-only output
  - temperature=0.1 for deterministic financial analysis
  - Robust JSON extraction (markdown fence → brace search fallback)
  - Pydantic AnalysisResponse validates and coerces all fields
  - tenacity retry on transient Gemini API errors (up to 3 attempts)
  - Tools registered with MCPServer — Gemini calls them autonomously
  - Structured logging throughout (no bare print)
  - Market sentiment analysis is wired up (was dead code before)
"""
import os
import re
import json
from typing import Any, Dict, List, Literal, Optional, TYPE_CHECKING
from datetime import datetime

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator, ValidationError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from utils.logger import get_logger

if TYPE_CHECKING:
    from agents.mcp_server import MCPServer

load_dotenv()
logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Pydantic response schemas — validate and coerce Gemini output before use
# ---------------------------------------------------------------------------

class AnalysisResponse(BaseModel):
    should_buy: bool
    confidence_level: Literal["High", "Medium", "Low"]
    target_price: float = Field(gt=0)
    stop_loss: float = Field(gt=0)
    time_horizon: str = "Medium term"
    key_reasons: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    overall_score: int = Field(ge=0, le=100)
    summary: str = ""

    @field_validator("target_price", "stop_loss", mode="before")
    @classmethod
    def coerce_price(cls, v):
        return round(float(v), 2)

    @field_validator("overall_score", mode="before")
    @classmethod
    def coerce_score(cls, v):
        return max(0, min(100, int(v)))

    @field_validator("key_reasons", "risks", mode="before")
    @classmethod
    def coerce_list(cls, v):
        if isinstance(v, list):
            return [str(x) for x in v[:5]]
        return []


class MarketSentimentResponse(BaseModel):
    overall_sentiment: Literal["Bullish", "Bearish", "Neutral"]
    confidence: Literal["High", "Medium", "Low"]
    key_factors: List[str] = Field(default_factory=list)
    outlook: str = ""


# ---------------------------------------------------------------------------
# Prompts / system instructions
# ---------------------------------------------------------------------------

SYSTEM_INSTRUCTION = (
    "You are an expert Indian stock market analyst specialising in NSE/BSE equities. "
    "Your analysis is data-driven, objective, and focused on swing trading (2–6 week horizon). "
    "When tools are available, call them to fetch up-to-date technical and fundamental data "
    "before forming your opinion. "
    "Your FINAL response MUST be a single valid JSON object matching the exact schema "
    "provided in the prompt. Do NOT wrap it in markdown fences. Do NOT add prose before or after."
)

MARKET_SENTIMENT_INSTRUCTION = (
    "You are an expert macroeconomic and equity market analyst. "
    "Analyse the provided market data and return ONLY a valid JSON object "
    "matching the schema in the prompt. No markdown, no prose."
)

# JSON schema shown to Gemini for the analysis output
_ANALYSIS_OUTPUT_SCHEMA = (
    "{\n"
    '  "should_buy": true | false,\n'
    '  "confidence_level": "High" | "Medium" | "Low",\n'
    '  "target_price": <number>,\n'
    '  "stop_loss": <number>,\n'
    '  "time_horizon": "Short term" | "Medium term" | "Long term",\n'
    '  "key_reasons": ["<reason>", ...],\n'
    '  "risks": ["<risk>", ...],\n'
    '  "overall_score": <integer 0–100>,\n'
    '  "summary": "<one sentence>"\n'
    "}"
)

# Tool declarations exposed to Gemini via function calling
TOOL_SCHEMAS: List[Dict[str, Any]] = [
    {
        "name": "get_technical_signals",
        "description": (
            "Fetch real-time technical indicator signals for a NSE/BSE stock symbol. "
            "Returns RSI, MACD, Bollinger Bands, moving average trend, stochastic, "
            "support/resistance levels, volatility, and overall sentiment."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "NSE symbol without exchange suffix, e.g. 'TCS'."
                }
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "get_fundamental_data",
        "description": (
            "Fetch fundamental financial data for a NSE/BSE stock symbol. "
            "Returns P/E, P/B, ROE, Debt/Equity, revenue growth, fundamental score (0–100), "
            "52-week high/low, company name, sector, and price trend analysis."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "NSE symbol without exchange suffix, e.g. 'TCS'."
                }
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "calculate_risk_reward",
        "description": (
            "Calculate risk-reward ratio for a trade setup. "
            "Returns ratio, potential profit %, risk %, and whether the setup is favorable."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "entry_price":  {"type": "number", "description": "Entry price in INR."},
                "target_price": {"type": "number", "description": "Target price in INR."},
                "stop_loss":    {"type": "number", "description": "Stop-loss price in INR."}
            },
            "required": ["entry_price", "target_price", "stop_loss"]
        }
    }
]


# ---------------------------------------------------------------------------
# AIAnalyzer
# ---------------------------------------------------------------------------

class AIAnalyzer:
    """
    Gemini-powered stock analyser using the google-genai SDK.

    Pass an MCPServer instance to enable the agentic tool-calling loop
    (Gemini autonomously fetches technical/fundamental data via tools).
    Without an MCPServer the analyser falls back to a one-shot prompt with
    pre-aggregated data, and further to deterministic rules if Gemini is down.
    """

    def __init__(self, mcp_server: Optional["MCPServer"] = None):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self._available = False
        self._client = None
        self._model_name: Optional[str] = None
        self.mcp_server = mcp_server

        if self.api_key:
            self._init_gemini()
        else:
            logger.warning("GEMINI_API_KEY not set — AI analysis disabled; rule-based fallback active.")

        if mcp_server is not None:
            self._register_tools(mcp_server)

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _init_gemini(self):
        try:
            from google import genai
            from google.genai import types as gtypes

            self._genai = genai
            self._gtypes = gtypes
            self._client = genai.Client(api_key=self.api_key)

            # Preference-ordered model list
            candidates = [
                "gemini-2.0-flash",
                "gemini-2.0-flash-lite",
                "gemini-1.5-pro",
                "gemini-1.5-flash",
                "gemini-pro",
            ]
            for name in candidates:
                try:
                    # Quick test — list models or just trust the name
                    self._model_name = name
                    self._available = True
                    logger.info("AI model selected: %s", name)
                    break
                except Exception:
                    continue

            if not self._available:
                logger.error("Could not select a Gemini model — AI disabled.")
        except Exception as e:
            logger.error("Gemini initialisation failed: %s", e)

    def _register_tools(self, mcp_server: "MCPServer"):
        """Register tool handlers with the MCPServer for the agentic loop."""
        from utils.technical_analyzer import TechnicalAnalyzer
        from utils.fundamental_analyzer import FundamentalAnalyzer
        from utils.risk_manager import RiskManager

        tech = TechnicalAnalyzer()
        fund = FundamentalAnalyzer()
        risk = RiskManager()

        def get_technical_signals(symbol: str) -> Dict[str, Any]:
            data = tech.get_stock_data(symbol)
            if data.empty:
                return {"error": f"No data for {symbol}"}
            return tech.analyze(data)

        def get_fundamental_data(symbol: str) -> Dict[str, Any]:
            return fund.analyze(symbol)

        def calculate_risk_reward(entry_price: float, target_price: float, stop_loss: float) -> Dict[str, Any]:
            result = risk.calculate_risk_reward(entry_price, target_price, stop_loss)
            return result if result else {"error": "Could not calculate risk-reward"}

        handlers = {
            "get_technical_signals": get_technical_signals,
            "get_fundamental_data":  get_fundamental_data,
            "calculate_risk_reward": calculate_risk_reward,
        }
        for schema in TOOL_SCHEMAS:
            mcp_server.register_tool(schema["name"], schema, handlers[schema["name"]])

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        return self._available

    def analyze_buying_opportunity(
        self,
        symbol: str,
        current_price: float,
        technical_signals: Dict[str, Any],
        fundamental_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Main entry point.  Runs the agentic loop when tools are available,
        falls back to single-shot prompt, then rule-based logic.
        """
        if not self._available:
            logger.info("[%s] AI unavailable — rule-based fallback.", symbol)
            return self._fallback_analysis(current_price, technical_signals, fundamental_data)

        try:
            if self.mcp_server is not None and self.mcp_server.tools:
                result = self._agentic_loop(symbol, current_price)
            else:
                result = self._single_shot_analysis(
                    symbol, current_price, technical_signals, fundamental_data
                )

            rule_based = self._fallback_analysis(current_price, technical_signals, fundamental_data)
            result.update({"ai_available": True, "rule_based_validation": rule_based})
            return result

        except Exception as e:
            logger.error("[%s] AI analysis failed: %s — falling back to rule-based.", symbol, e)
            return self._fallback_analysis(current_price, technical_signals, fundamental_data)

    def analyze_market_sentiment(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse overall market sentiment from aggregated market data."""
        if not self._available:
            return self._simple_market_analysis()
        try:
            prompt = (
                "Analyse the following Indian stock market data and return a JSON object "
                "with EXACTLY these keys: overall_sentiment (Bullish/Bearish/Neutral), "
                "confidence (High/Medium/Low), key_factors (array of strings), outlook (string).\n\n"
                f"Market Data:\n{json.dumps(market_data, default=str, indent=2)}"
            )
            text = self._call_gemini(
                prompt,
                system_instruction=MARKET_SENTIMENT_INSTRUCTION,
                use_tools=False,
            )
            data = self._extract_json(text)
            return MarketSentimentResponse(**data).model_dump()
        except Exception as e:
            logger.error("Market sentiment analysis failed: %s", e)
            return self._simple_market_analysis()

    # ------------------------------------------------------------------
    # Agentic loop — Gemini calls tools autonomously
    # ------------------------------------------------------------------

    def _agentic_loop(self, symbol: str, current_price: float) -> Dict[str, Any]:
        """
        Multi-turn conversation where Gemini decides which tools to call.
        Loop guard: max 6 turns to prevent infinite cycles.
        """
        from google.genai import types as gtypes

        # Build FunctionDeclarations from our TOOL_SCHEMAS
        fn_decls = []
        for s in TOOL_SCHEMAS:
            props = {}
            for pname, pdef in s["parameters"].get("properties", {}).items():
                ptype = (
                    gtypes.Type.STRING if pdef.get("type") == "string"
                    else gtypes.Type.NUMBER
                )
                props[pname] = gtypes.Schema(
                    type=ptype,
                    description=pdef.get("description", ""),
                )
            fn_decls.append(
                gtypes.FunctionDeclaration(
                    name=s["name"],
                    description=s["description"],
                    parameters=gtypes.Schema(
                        type=gtypes.Type.OBJECT,
                        properties=props,
                        required=s["parameters"].get("required", []),
                    ),
                )
            )

        tools = [gtypes.Tool(function_declarations=fn_decls)]
        config = gtypes.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.1,
            max_output_tokens=2048,
            tools=tools,
        )

        initial_prompt = (
            f"Analyse {symbol} (current price ₹{current_price:.2f}) as a swing trading opportunity.\n"
            "Use the available tools to fetch technical signals and fundamental data before deciding.\n"
            "After reviewing the tool results, return your final answer as a JSON object "
            f"matching this exact schema:\n{_ANALYSIS_OUTPUT_SCHEMA}"
        )

        # Build up the conversation as a list of Content objects
        contents = [gtypes.Content(role="user", parts=[gtypes.Part(text=initial_prompt)])]
        max_turns = 6

        for turn in range(max_turns):
            response = self._call_gemini_contents(contents, config)
            candidate = response.candidates[0]

            # Collect all function call parts
            fn_calls = [
                part.function_call
                for part in candidate.content.parts
                if hasattr(part, "function_call") and part.function_call
            ]

            if not fn_calls:
                # Final answer — extract and validate JSON
                text = "".join(
                    part.text
                    for part in candidate.content.parts
                    if hasattr(part, "text") and part.text
                )
                data = self._extract_json(text)
                validated = AnalysisResponse(**data)
                result = validated.model_dump()
                result["analysis_method"] = "agentic_loop"
                result["turns_used"] = turn + 1
                logger.info("[%s] Agentic loop complete in %d turn(s).", symbol, turn + 1)
                return result

            # Append the model's function-call turn to conversation history
            contents.append(candidate.content)

            # Execute each tool and build function-response parts
            response_parts = []
            for fc in fn_calls:
                tool_name = fc.name
                args = dict(fc.args)
                logger.info("[%s] Gemini calling tool: %s(%s)", symbol, tool_name, args)
                tool_resp = self.mcp_server.call_tool(tool_name, args)
                tool_result = tool_resp.get("result", tool_resp)
                response_parts.append(
                    gtypes.Part(
                        function_response=gtypes.FunctionResponse(
                            name=tool_name,
                            response={"result": json.loads(json.dumps(tool_result, default=str))},
                        )
                    )
                )

            contents.append(
                gtypes.Content(role="user", parts=response_parts)
            )

        logger.warning("[%s] Agentic loop exceeded %d turns — falling back to single-shot.", symbol, max_turns)
        raise RuntimeError("Agentic loop exceeded max turns")

    # ------------------------------------------------------------------
    # Single-shot analysis (pre-aggregated data inlined in prompt)
    # ------------------------------------------------------------------

    def _single_shot_analysis(
        self,
        symbol: str,
        current_price: float,
        technical_signals: Dict[str, Any],
        fundamental_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        prompt = self._build_analysis_prompt(symbol, current_price, technical_signals, fundamental_data)
        text = self._call_gemini(prompt)
        data = self._extract_json(text)
        validated = AnalysisResponse(**data)
        result = validated.model_dump()
        result["analysis_method"] = "single_shot"
        return result

    def _build_analysis_prompt(
        self,
        symbol: str,
        current_price: float,
        technical_signals: Dict[str, Any],
        fundamental_data: Dict[str, Any],
    ) -> str:
        sr    = technical_signals.get("support_resistance", {})
        sigs  = technical_signals.get("signals", {})
        ratios = fundamental_data.get("financial_ratios", {})
        pa    = fundamental_data.get("price_analysis", {})
        fs    = fundamental_data.get("fundamental_score", {})

        few_shot = (
            '{"should_buy":true,"confidence_level":"High","target_price":3500.00,'
            '"stop_loss":3100.00,"time_horizon":"Medium term",'
            '"key_reasons":["RSI oversold","Strong ROE","Price near 52W low"],'
            '"risks":["High D/E ratio"],"overall_score":78,'
            '"summary":"Technically and fundamentally attractive entry."}'
        )

        return (
            f"Analyse {symbol} as a swing trading opportunity.\n\n"
            f"Stock: {symbol}  |  Current Price: ₹{current_price:.2f}\n\n"
            "TECHNICAL SIGNALS:\n"
            f"  Overall Sentiment : {technical_signals.get('overall_sentiment', 'Unknown')}\n"
            f"  RSI               : {technical_signals.get('rsi', 'N/A')} "
            f"(Signal: {sigs.get('rsi_signal', 'N/A')})\n"
            f"  MACD Signal       : {sigs.get('macd_signal', 'N/A')}\n"
            f"  Trend Signal      : {sigs.get('trend_signal', 'N/A')}\n"
            f"  Bollinger Bands   : {sigs.get('bb_signal', 'N/A')}\n"
            f"  Support           : ₹{sr.get('support', 'N/A')}\n"
            f"  Resistance        : ₹{sr.get('resistance', 'N/A')}\n"
            f"  Volatility        : {technical_signals.get('volatility', 'N/A')}\n\n"
            "FUNDAMENTAL DATA:\n"
            f"  Company           : {fundamental_data.get('company_name', symbol)}\n"
            f"  Sector            : {fundamental_data.get('sector_info', {}).get('sector', 'Unknown')}\n"
            f"  P/E               : {ratios.get('pe_ratio', 'N/A')}\n"
            f"  P/B               : {ratios.get('pb_ratio', 'N/A')}\n"
            f"  ROE               : {ratios.get('roe', 'N/A')}\n"
            f"  Debt/Equity       : {ratios.get('debt_to_equity', 'N/A')}\n"
            f"  Revenue Growth    : {ratios.get('revenue_growth', 'N/A')}\n"
            f"  Fundamental Score : {fs.get('score', 'N/A')}/100\n"
            f"  52W High / Low    : ₹{pa.get('52_week_high', 'N/A')} / ₹{pa.get('52_week_low', 'N/A')}\n\n"
            f"Example of valid output (do NOT copy values, only structure):\n{few_shot}\n\n"
            f"Return your analysis as a JSON object matching this schema:\n{_ANALYSIS_OUTPUT_SCHEMA}"
        )

    # ------------------------------------------------------------------
    # Gemini call helpers (with retry)
    # ------------------------------------------------------------------

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        before_sleep=before_sleep_log(logger, 20),  # 20 = logging.WARNING
        reraise=True,
    )
    def _call_gemini(
        self,
        prompt: str,
        system_instruction: str = SYSTEM_INSTRUCTION,
        use_tools: bool = False,
    ) -> str:
        from google.genai import types as gtypes

        config_kwargs: Dict[str, Any] = {
            "system_instruction": system_instruction,
            "temperature": 0.1,
            "max_output_tokens": 2048,
        }
        if use_tools and self.mcp_server and self.mcp_server.tools:
            fn_decls = self._build_fn_declarations()
            config_kwargs["tools"] = [gtypes.Tool(function_declarations=fn_decls)]

        config = gtypes.GenerateContentConfig(**config_kwargs)
        response = self._client.models.generate_content(
            model=self._model_name,
            contents=prompt,
            config=config,
        )
        return response.text

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        before_sleep=before_sleep_log(logger, 20),
        reraise=True,
    )
    def _call_gemini_contents(self, contents, config):
        return self._client.models.generate_content(
            model=self._model_name,
            contents=contents,
            config=config,
        )

    def _build_fn_declarations(self):
        from google.genai import types as gtypes
        decls = []
        for s in TOOL_SCHEMAS:
            props = {}
            for pname, pdef in s["parameters"].get("properties", {}).items():
                ptype = (
                    gtypes.Type.STRING if pdef.get("type") == "string"
                    else gtypes.Type.NUMBER
                )
                props[pname] = gtypes.Schema(type=ptype, description=pdef.get("description", ""))
            decls.append(gtypes.FunctionDeclaration(
                name=s["name"],
                description=s["description"],
                parameters=gtypes.Schema(
                    type=gtypes.Type.OBJECT,
                    properties=props,
                    required=s["parameters"].get("required", []),
                ),
            ))
        return decls

    # ------------------------------------------------------------------
    # JSON extraction
    # ------------------------------------------------------------------

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        Robustly extract a JSON object from LLM response text.
        Tries markdown code fence first, then brace-scan fallback.
        """
        # 1. Markdown code fence
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # 2. Brace scan
        start = text.find("{")
        end   = text.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError as e:
                raise ValueError(f"JSON decode failed after brace-scan: {e}") from e

        raise ValueError("No JSON object found in AI response")

    # ------------------------------------------------------------------
    # Rule-based fallback (no LLM dependency)
    # ------------------------------------------------------------------

    def _fallback_analysis(
        self,
        current_price: float,
        technical_signals: Dict[str, Any],
        fundamental_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        try:
            buy_signals = 0.0
            total_signals = 0
            reasons: List[str] = []
            risks: List[str] = []

            for name, value in technical_signals.get("signals", {}).items():
                total_signals += 1
                label = name.replace("_", " ").title()
                if value == "BUY":
                    buy_signals += 1
                    reasons.append(f"Technical: {label} shows BUY")
                elif value == "SELL":
                    risks.append(f"Technical: {label} shows SELL")

            rsi = technical_signals.get("rsi", 50) or 50
            if rsi < 30:
                buy_signals += 0.5
                reasons.append("RSI indicates oversold condition")
            elif rsi > 70:
                risks.append("RSI indicates overbought condition")

            fund_score = fundamental_data.get("fundamental_score", {}).get("score", 50)
            if fund_score >= 70:
                buy_signals += 1
                reasons.append("Strong fundamental score")
            elif fund_score <= 30:
                risks.append("Weak fundamental indicators")

            pe = fundamental_data.get("financial_ratios", {}).get("pe_ratio")
            if pe and 10 <= pe <= 25:
                buy_signals += 0.5
                reasons.append("Reasonable P/E ratio")
            elif pe and pe > 40:
                risks.append("High P/E ratio")

            pa = fundamental_data.get("price_analysis", {})
            h52, l52 = pa.get("52_week_high"), pa.get("52_week_low")
            if h52 and l52 and h52 != l52:
                pos = (current_price - l52) / (h52 - l52)
                if pos < 0.3:
                    buy_signals += 0.5
                    reasons.append("Price near 52-week low — potential value entry")
                elif pos > 0.8:
                    risks.append("Price near 52-week high")

            signal_strength = buy_signals / max(total_signals, 1)
            has_bullish = technical_signals.get("overall_sentiment") == "BULLISH"
            strong_fund = fund_score >= 60

            should_buy = (
                (signal_strength > 0.5 and len(reasons) >= len(risks))
                or (buy_signals > 0 and strong_fund)
                or (has_bullish and buy_signals > 0 and len(reasons) >= len(risks))
            )

            if signal_strength > 0.7 and strong_fund and has_bullish:
                confidence = "High"
            elif signal_strength > 0.5 and (strong_fund or has_bullish):
                confidence = "Medium"
            elif should_buy:
                confidence = "Medium"
            else:
                confidence = "Low"

            sr = technical_signals.get("support_resistance", {})
            support    = float(sr.get("support",    current_price * 0.95))
            resistance = float(sr.get("resistance", current_price * 1.10))
            target_price = min(resistance * 0.95, current_price * 1.15)
            stop_loss    = max(support    * 1.05, current_price * 0.95)
            overall_score = min(100, max(0, int(signal_strength * 100)))

            return {
                "should_buy":       should_buy,
                "confidence_level": confidence,
                "target_price":     round(target_price, 2),
                "stop_loss":        round(stop_loss, 2),
                "time_horizon":     "Medium term",
                "key_reasons":      reasons[:3],
                "risks":            risks[:3],
                "overall_score":    overall_score,
                "summary": (
                    f"Rule-based: {'BUY' if should_buy else 'HOLD/AVOID'} — "
                    f"{confidence.lower()} confidence."
                ),
                "signal_strength":  signal_strength,
                "ai_available":     False,
                "analysis_type":    "rule_based",
            }

        except Exception as e:
            logger.error("Fallback analysis error: %s", e)
            return self._default_analysis(current_price)

    def _default_analysis(self, current_price: float) -> Dict[str, Any]:
        return {
            "should_buy":       False,
            "confidence_level": "Low",
            "target_price":     round(current_price * 1.05, 2),
            "stop_loss":        round(current_price * 0.97, 2),
            "time_horizon":     "Short term",
            "key_reasons":      ["AI analysis unavailable"],
            "risks":            ["Unable to perform comprehensive analysis"],
            "overall_score":    50,
            "summary":          "AI analysis failed — using conservative defaults.",
            "ai_available":     False,
            "analysis_type":    "default",
        }

    def _simple_market_analysis(self) -> Dict[str, Any]:
        return {
            "overall_sentiment": "Neutral",
            "confidence":        "Medium",
            "key_factors":       ["Insufficient data for detailed analysis"],
            "outlook":           "Market analysis requires more comprehensive data.",
            "ai_available":      self._available,
        }
