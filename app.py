import re
import os
import json
import logging
from datetime import datetime, timedelta

import numpy as np
from flask import Flask, render_template, request, jsonify, flash
from flask_cors import CORS
from dotenv import load_dotenv

from utils.kite_handler import KiteHandler
from agents.orchestrator import AgentOrchestrator
from utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

app = Flask(__name__)

# Secret key — must be set in environment; refuse to start with insecure default in production
_secret = os.getenv("FLASK_SECRET_KEY")
if not _secret:
    if os.getenv("FLASK_ENV") == "production":
        raise RuntimeError(
            "FLASK_SECRET_KEY environment variable must be set in production. "
            "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    _secret = "dev-only-insecure-key-change-before-deploy"
    logger.warning("FLASK_SECRET_KEY not set — using insecure dev key. Set it before deploying.")

app.secret_key = _secret
CORS(app)

# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

kite_handler: KiteHandler = None
agent_orchestrator: AgentOrchestrator = None


def initialize_handlers():
    global kite_handler, agent_orchestrator

    try:
        kite_handler = KiteHandler()
        if kite_handler.is_connected():
            logger.info("Kite integration enabled — portfolio features available.")
        else:
            logger.info("Kite not connected — running in analysis-only mode.")
    except Exception as e:
        logger.info("Kite integration disabled: %s — analysis-only mode.", e)

    agent_orchestrator = AgentOrchestrator(kite_handler)
    logger.info("Multi-Agent Orchestrator initialised.")


initialize_handlers()

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

# Valid NSE/BSE symbol pattern
_SYMBOL_RE = re.compile(r'^[A-Z0-9&.\-]{1,20}$')


def _validate_symbol(raw: str):
    """Return sanitised uppercase symbol or raise ValueError."""
    symbol = raw.strip().upper()
    if not symbol:
        raise ValueError("symbol is required")
    if not _SYMBOL_RE.match(symbol):
        raise ValueError(
            f"Invalid symbol '{symbol}'. Use 1–20 uppercase letters/digits/&/./- only."
        )
    return symbol


def convert_numpy_types(obj):
    """Recursively convert NumPy scalars/arrays to Python native types for JSON."""
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_numpy_types(i) for i in obj]
    if isinstance(obj, tuple):
        return tuple(convert_numpy_types(i) for i in obj)
    return obj


# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("sector_analysis.html")


@app.route("/analyze-stock")
def analyze_stock_page():
    return render_template("index.html")


@app.route("/recommendations")
def recommendations():
    return render_template("recommendations.html")


@app.route("/sector-analysis")
def sector_analysis():
    return render_template("sector_analysis.html")


@app.route("/portfolio")
def portfolio():
    try:
        holdings_result = agent_orchestrator.mcp_server.route_request("portfolio", {
            "action": "get_holdings"
        })
        positions_result = agent_orchestrator.mcp_server.route_request("portfolio", {
            "action": "get_positions"
        })

        if not holdings_result.get("success"):
            flash("Portfolio data not available. Please check Kite API connection.", "warning")
            return render_template("portfolio.html", holdings=[], positions=[])

        holdings = holdings_result.get("data", {}).get("holdings", [])
        positions = positions_result.get("data", {}).get("positions", []) if positions_result.get("success") else []
        return render_template("portfolio.html", holdings=holdings, positions=positions)

    except Exception as e:
        flash(f"Error fetching portfolio: {e}", "error")
        return render_template("portfolio.html", holdings=[], positions=[])


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

@app.route("/analyze", methods=["POST"])
def analyze_stock():
    try:
        data = request.get_json(silent=True) or {}
        symbol = _validate_symbol(data.get("symbol", ""))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    try:
        result = agent_orchestrator.analyze_stock(symbol)
        if "error" in result:
            return jsonify(result), 500

        result = convert_numpy_types(result)
        result["timestamp"] = datetime.now().isoformat()
        return jsonify(result)

    except Exception as e:
        logger.error("Analysis error for %s: %s", symbol, e, exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/recommendations", methods=["GET", "POST"])
def get_recommendations():
    try:
        if request.method == "POST":
            data = request.get_json(silent=True) or {}
            raw_symbols = data.get("symbols")
            min_score = int(data.get("min_score", 60))
            max_results = int(data.get("max_results", 20))
        else:
            raw_symbols = request.args.get("symbols")
            min_score = int(request.args.get("min_score", 60))
            max_results = int(request.args.get("max_results", 20))

        # Validate and sanitise custom symbol list
        symbols = None
        if raw_symbols:
            raw_list = raw_symbols if isinstance(raw_symbols, list) else raw_symbols.split(",")
            try:
                symbols = [_validate_symbol(s) for s in raw_list]
            except ValueError as e:
                return jsonify({"error": str(e)}), 400

        result = agent_orchestrator.scan_stocks(
            symbols=symbols, min_score=min_score, max_results=max_results
        )
        if "error" in result:
            return jsonify(result), 500

        result = convert_numpy_types(result)
        result["scanned_at"] = datetime.now().isoformat()
        return jsonify(result)

    except Exception as e:
        logger.error("Recommendations error: %s", e, exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/sell-recommendations")
def sell_recommendations():
    try:
        result = agent_orchestrator.mcp_server.route_request("portfolio", {
            "action": "get_sell_recommendations"
        })
        if not result.get("success"):
            return jsonify({"error": result.get("error", "Portfolio not available")}), 503
        return jsonify(result.get("data", {}))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/sector-analysis")
def get_sector_analysis():
    try:
        sector_stocks = {
            "Technology":  ["TCS", "INFY"],
            "Banking":     ["HDFCBANK", "ICICIBANK"],
            "Energy":      ["RELIANCE", "ONGC"],
            "FMCG":        ["HINDUNILVR", "ITC"],
            "Automobile":  ["MARUTI", "TATAMOTORS"],
        }

        sectors_data = []
        for sector_name, syms in sector_stocks.items():
            stocks_data = []
            for symbol in syms:
                try:
                    analysis = agent_orchestrator.analyze_stock(symbol)
                    if "error" in analysis:
                        continue

                    technical = analysis.get("technical_analysis", {})
                    buying = analysis.get("buying_analysis", {})
                    fundamental = analysis.get("fundamental_analysis", {})
                    signals = technical.get("signals", {})

                    buy_s  = sum(1 for v in signals.values() if v == "BUY")
                    sell_s = sum(1 for v in signals.values() if v == "SELL")
                    hold_s = sum(1 for v in signals.values() if v == "HOLD")
                    total_s = buy_s + sell_s + hold_s

                    if total_s > 0:
                        buy_pct  = (buy_s  / total_s) * 100
                        sell_pct = (sell_s / total_s) * 100
                        neutral_pct = (hold_s / total_s) * 100
                    else:
                        should_buy = buying.get("should_buy", False)
                        confidence = buying.get("confidence_level", "Low")
                        if should_buy:
                            buy_pct  = 60 if confidence == "High" else 50 if confidence == "Medium" else 40
                            sell_pct = 20
                        else:
                            sell_pct = 50
                            buy_pct  = 20
                        neutral_pct = max(0, 100 - buy_pct - sell_pct)

                    sentiment = technical.get("overall_sentiment", "NEUTRAL")
                    if sentiment == "BULLISH":
                        buy_pct  = min(100, buy_pct  + 15)
                        sell_pct = max(0,   sell_pct - 10)
                    elif sentiment == "BEARISH":
                        sell_pct = min(100, sell_pct + 15)
                        buy_pct  = max(0,   buy_pct  - 10)

                    total = buy_pct + sell_pct + neutral_pct
                    if total > 0:
                        buy_pct     = (buy_pct     / total) * 100
                        sell_pct    = (sell_pct    / total) * 100
                        neutral_pct = (neutral_pct / total) * 100

                    sig_count = len(signals) or 1
                    tech_score = 50.0 + (
                        (buy_s - sell_s) / sig_count
                    ) * 30.0

                    stocks_data.append({
                        "symbol": symbol,
                        "company_name": fundamental.get("company_name", symbol),
                        "current_price": float(analysis.get("current_price", 0)),
                        "ratings": {
                            "buy":     float(buy_pct),
                            "sell":    float(sell_pct),
                            "neutral": float(neutral_pct),
                        },
                        "technical_score":   float(max(0, min(100, tech_score))),
                        "fundamental_score": float(fundamental.get("fundamental_score", {}).get("score", 50)),
                        "overall_sentiment": sentiment,
                    })
                except Exception as e:
                    logger.warning("Sector analysis error for %s: %s", symbol, e)
                    continue

            if stocks_data:
                sectors_data.append({"sector_name": sector_name, "stocks": stocks_data})

        sectors_data = convert_numpy_types(sectors_data)
        return jsonify({
            "sectors": sectors_data,
            "total_sectors": len(sectors_data),
            "analyzed_at": datetime.now().isoformat(),
        })

    except Exception as e:
        logger.error("Sector analysis error: %s", e, exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/market-sentiment")
def get_market_sentiment():
    """Return overall market sentiment based on a sample of large-cap stocks."""
    try:
        sample_symbols = ["NIFTY50", "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"]
        market_data = {
            "sample_symbols": sample_symbols,
            "timestamp": datetime.now().isoformat(),
        }

        # Enrich with quick price checks for the available stocks
        for sym in sample_symbols[1:]:
            try:
                result = agent_orchestrator.mcp_server.route_request("stock_search", {
                    "action": "search", "symbol": sym
                })
                if result.get("success"):
                    market_data[sym] = {
                        "price": result["data"]["current_price"]
                    }
            except Exception:
                pass

        sentiment = agent_orchestrator.ai_agent.ai_analyzer.analyze_market_sentiment(market_data)
        sentiment = convert_numpy_types(sentiment)
        sentiment["analyzed_at"] = datetime.now().isoformat()
        return jsonify(sentiment)

    except Exception as e:
        logger.error("Market sentiment error: %s", e, exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/status")
def api_status():
    agent_status = agent_orchestrator.get_agent_status()
    status = {
        "kite_connected":      kite_handler.is_connected() if kite_handler else False,
        "portfolio_available": (
            agent_orchestrator.portfolio_agent.is_connected()
            if agent_orchestrator.portfolio_agent else False
        ),
        "mcp_server":          agent_status.get("mcp_server"),
        "total_agents":        agent_status.get("total_agents"),
        "tools_registered":    agent_status.get("tools_registered"),
        "tool_names":          agent_status.get("tool_names", []),
        "agents":              agent_status.get("agents"),
        "services": {
            "technical_analysis":  True,
            "fundamental_analysis": True,
            "ai_analysis":         agent_orchestrator.ai_agent.ai_analyzer.is_available(),
            "risk_management":     True,
            "stock_search":        True,
            "multi_agent_system":  True,
        },
    }
    return jsonify(status)


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template("500.html"), 500


# ---------------------------------------------------------------------------
# Entry point (dev only — production uses gunicorn via Procfile)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV") == "development"
    app.run(debug=debug, host="0.0.0.0", port=port)
