# Trading Analysis App - Multi-Agent System

A comprehensive **multi-agent trading analysis application** using **Model Context Protocol (MCP)** for analyzing Indian stocks. The system uses specialized AI agents for different aspects of stock analysis, all coordinated through an MCP server.

**✨ Works WITHOUT Zerodha Account** - Full stock analysis capabilities available without any broker integration!

## 🤖 Multi-Agent Architecture

This application uses a **multi-agent system** with **Model Context Protocol (MCP)** for agent communication and coordination. Each agent specializes in a specific domain:

### Agent Overview

1. **Stock Search Agent** (`stock_search`)
   - Searches and validates stock symbols
   - Scans multiple stocks for availability
   - Validates stock data accessibility

2. **Technical Analysis Agent** (`technical_analysis`)
   - Calculates technical indicators (RSI, MACD, Bollinger Bands)
   - Generates buy/sell signals
   - Analyzes price trends and support/resistance levels

3. **Fundamental Analysis Agent** (`fundamental_analysis`)
   - Fetches company financial data
   - Calculates financial ratios (P/E, P/B, ROE, etc.)
   - Analyzes company fundamentals and sector information

4. **Risk Management Agent** (`risk_management`)
   - Calculates risk-reward ratios
   - Determines position sizing
   - Analyzes portfolio risk

5. **AI Analysis Agent** (`ai_analysis`)
   - Provides AI-powered buy/sell recommendations
   - Uses Google Gemini AI for intelligent analysis
   - Generates confidence scores and reasoning

6. **Portfolio Agent** (`portfolio`)
   - Manages portfolio holdings and positions
   - Provides sell recommendations
   - Tracks P&L (requires Zerodha Kite API)

### MCP Server

The **Model Context Protocol (MCP) Server** coordinates all agents:
- Routes requests to appropriate agents
- Manages agent communication
- Tracks agent status and execution history
- Provides unified API for agent interactions

### Agent Orchestrator

The **Agent Orchestrator** coordinates multi-agent workflows:
- Orchestrates complex analysis pipelines
- Combines results from multiple agents
- Manages agent dependencies and sequencing
- Provides high-level analysis functions

## 🚀 Quick Start (5 Minutes Setup!)

```bash
# 1. Clone and setup
git clone <repository-url>
cd trading_analysis_app
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app (no configuration needed!)
python app.py

# 4. Open browser: http://localhost:5000

# That's it! Start analyzing stocks with Yahoo Finance data (free!)
```

**Optional**: Add Gemini API key for AI-powered insights (free from https://aistudio.google.com)

## Features

### 🔍 Stock Analysis (No Broker Account Needed!)
- **Multi-Agent Technical Analysis**: RSI, MACD, Bollinger Bands, Moving Averages, Support/Resistance levels
- **Multi-Agent Fundamental Analysis**: P/E, P/B, ROE, Debt/Equity ratios, Revenue growth, Company financials
- **AI-Powered Insights**: Buy/sell recommendations using Google Gemini AI via AI Analysis Agent
- **Risk-Reward Calculations**: Automatic 1:2 risk-reward ratio analysis via Risk Management Agent
- **Position Sizing**: Intelligent position size recommendations based on capital
- **Data Source**: Yahoo Finance (completely free!)

### 📊 Portfolio Management (Optional - Requires Zerodha Account)
- **Live Portfolio Sync**: Real-time sync with Zerodha Kite account via Portfolio Agent
- **Holdings & Positions**: View current holdings and day trading positions
- **P&L Tracking**: Detailed profit/loss analysis
- **Sell Recommendations**: AI-powered suggestions on when to sell based on 1:2 risk-reward
- **Note**: Portfolio features are OPTIONAL. App works perfectly without them!

### 🤖 Multi-Agent System Features
- **Agent Coordination**: MCP-based agent communication
- **Specialized Agents**: Each agent handles specific domain expertise
- **Scalable Architecture**: Easy to add new agents or extend existing ones
- **Agent Status Tracking**: Monitor agent health and execution history
- **Parallel Processing**: Agents can work independently and in parallel

## 🚀 Technology Stack

- **Backend**: Python Flask
- **Multi-Agent System**: Custom MCP (Model Context Protocol) implementation
- **APIs**: Zerodha Kite Connect, Yahoo Finance, Google Gemini AI
- **Frontend**: Bootstrap 5, JavaScript, Chart.js
- **Analysis**: TA-Lib, Pandas, NumPy
- **Agents**: 6 specialized agents for different analysis domains
- **Deployment**: Can be deployed on any cloud platform

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Flask Web App                         │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              Agent Orchestrator                         │
│         (Coordinates Multi-Agent Workflows)             │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                   MCP Server                             │
│      (Model Context Protocol - Agent Communication)      │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Stock Search │ │  Technical   │ │ Fundamental  │
│    Agent     │ │    Agent     │ │    Agent     │
└──────────────┘ └──────────────┘ └──────────────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Risk Mgmt    │ │  AI Analysis │ │  Portfolio   │
│    Agent     │ │    Agent     │ │    Agent     │
└──────────────┘ └──────────────┘ └──────────────┘
```

## Prerequisites

### Required (for basic stock analysis):
1. **Python 3.8+**: Required for running the application
2. **Google Gemini API** (Optional but recommended): Free API key from Google AI Studio for AI-powered insights

### Optional (only if you want portfolio features):
3. **Zerodha Trading Account**: Active Zerodha account (ONLY needed for portfolio management)
4. **Kite Connect API**: API subscription from Zerodha (₹2000/month + GST - ONLY if you need portfolio features)

**💡 TIP: Start without Zerodha! Use the app for free stock analysis first, add portfolio features later if needed.**

## Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd trading_analysis_app
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables (Optional)

Create a `.env` file in the root directory:

```bash
touch .env
```

**Minimal Setup (Recommended to Start):**
```env
# Optional but recommended - for AI insights
GEMINI_API_KEY=your_gemini_api_key_here

# Flask Configuration (optional, has defaults)
FLASK_SECRET_KEY=some_random_secret_key
FLASK_ENV=development
```

**Full Setup (If you want portfolio features):**
```env
# Zerodha Kite API Credentials (OPTIONAL - only for portfolio features)
KITE_API_KEY=your_kite_api_key_here
KITE_API_SECRET=your_kite_api_secret_here
KITE_ACCESS_TOKEN=your_access_token_here

# Gemini AI API Key (optional but recommended)
GEMINI_API_KEY=your_gemini_api_key_here

# Flask Configuration
FLASK_SECRET_KEY=your_secret_key_here
FLASK_ENV=development
```

### 5. Get API Credentials (Optional)

#### Google Gemini API (Free - Recommended):
1. Visit [Google AI Studio](https://aistudio.google.com)
2. Click "Get API Key"
3. Copy the API key to your `.env` file as `GEMINI_API_KEY`

#### Zerodha Kite API (ONLY if you need portfolio features):
**⚠️ WARNING: This is complex and expensive (₹2000/month). Skip unless you specifically need portfolio integration.**

1. Visit [Kite Connect](https://kite.zerodha.com/connect/login)
2. Create an app and get `API_KEY` and `API_SECRET`
3. Generate `ACCESS_TOKEN` using the helper script:
   ```bash
   python -c "from utils.kite_handler import KiteHandler; KiteHandler.generate_access_token('your_api_key', 'your_api_secret')"
   ```
4. Follow the prompts to login and generate the token
5. **Note**: Access token expires DAILY at 7:30 AM and must be regenerated

## Running the Application

### Development Mode
```bash
python app.py
```

The application will be available at `http://localhost:5000`

### Production Deployment
```bash
gunicorn --bind 0.0.0.0:5000 app:app
```

## Usage Guide

### 1. Stock Analysis (Multi-Agent Pipeline)
1. Enter a stock symbol (e.g., RELIANCE, TCS, INFY)
2. Click "Analyze Stock"
3. The system orchestrates multiple agents:
   - **Stock Search Agent**: Validates and fetches stock data
   - **Technical Analysis Agent**: Calculates technical indicators
   - **Fundamental Analysis Agent**: Analyzes company fundamentals
   - **AI Analysis Agent**: Provides AI-powered recommendations
   - **Risk Management Agent**: Calculates risk-reward ratios
4. View comprehensive analysis including:
   - Current price and AI recommendation
   - Technical indicators and signals
   - Fundamental ratios and company data
   - Risk-reward analysis with target and stop-loss prices
   - Position size recommendations

### 2. Buy Recommendations (Multi-Agent Scanning)
1. Navigate to "Buy Recommendations" section
2. The system uses multiple agents to scan stocks:
   - **Stock Search Agent**: Scans available stocks
   - **Technical/Fundamental/AI Agents**: Analyze each stock
   - **Risk Management Agent**: Calculates risk-reward
3. View recommendations with:
   - Buy price, target price, stop loss
   - Risk-reward ratios
   - Timeline for swing trading
   - Analysis scores from multiple agents

### 3. Portfolio Management (Portfolio Agent)
1. Navigate to "Portfolio" section
2. **Portfolio Agent** fetches your holdings and positions
3. Check P&L for each stock
4. Get sell recommendations based on 1:2 risk-reward ratio
5. Analyze individual stocks directly from portfolio

### 4. Agent Status
Visit `/api/status` to see:
- Status of all agents
- MCP server information
- Agent execution counts
- Service availability

## API Endpoints

### Stock Analysis (Multi-Agent)
- `POST /analyze` - Analyze a stock symbol (uses all agents)
- `GET /api/status` - Check agent status and MCP server info

### Buy Recommendations (Multi-Agent Scanning)
- `GET /recommendations` - View recommendations page
- `POST /api/recommendations` - Get buy recommendations (uses multiple agents)

### Portfolio Management (Portfolio Agent)
- `GET /portfolio` - View portfolio page
- `GET /sell-recommendations` - Get sell recommendations

## Multi-Agent System Architecture

### Agent Communication Flow

```
User Request
    │
    ▼
Agent Orchestrator
    │
    ▼
MCP Server (Routes to appropriate agents)
    │
    ├──► Stock Search Agent
    ├──► Technical Analysis Agent
    ├──► Fundamental Analysis Agent
    ├──► Risk Management Agent
    ├──► AI Analysis Agent
    └──► Portfolio Agent
    │
    ▼
Results Aggregated
    │
    ▼
Response to User
```

### Adding New Agents

To add a new agent:

1. Create agent class in `agents/` directory:
```python
from agents.base_agent import BaseAgent

class MyNewAgent(BaseAgent):
    def __init__(self):
        super().__init__("my_agent", "My New Agent")
    
    def process(self, context):
        # Your agent logic here
        return self.create_response(True, data={...})
```

2. Register in orchestrator:
```python
self.mcp_server.register_agent("my_agent", MyNewAgent())
```

3. Use in workflows:
```python
result = self.mcp_server.route_request("my_agent", {...})
```

## Configuration Options

### Risk Management Settings
Edit `utils/risk_manager.py` to customize:
- Default risk per trade (default: 2%)
- Target risk-reward ratio (default: 1:2)
- Stop-loss percentages
- Position sizing algorithms

### Technical Analysis Parameters
Edit `utils/technical_analyzer.py` to modify:
- RSI periods and thresholds
- MACD parameters
- Bollinger Bands settings
- Moving average periods

### AI Analysis Prompts
Edit `utils/ai_analyzer.py` to customize:
- Analysis prompts for Gemini AI
- Confidence thresholds
- Recommendation criteria

### Agent Configuration
Edit `agents/orchestrator.py` to:
- Modify agent coordination logic
- Add new agent workflows
- Customize agent communication

## FAQ

### What is MCP (Model Context Protocol)?
MCP is a protocol for agent communication and coordination. In this app, it enables different specialized agents to communicate and work together seamlessly.

### How does the multi-agent system work?
Each agent specializes in a specific domain (technical analysis, fundamental analysis, etc.). The Agent Orchestrator coordinates these agents to perform complex analysis tasks.

### Can I add custom agents?
Yes! The architecture is designed to be extensible. See "Adding New Agents" section above.

### Do I need a Zerodha account to use this app?
**No!** The app works perfectly without Zerodha. All stock analysis features use free Yahoo Finance data. Zerodha is only needed if you want portfolio management features.

### What's the deal with the Kite API token?
Zerodha Kite Connect API requires:
1. **API Key & Secret** - Available on Kite Console
2. **Access Token** - Generated via OAuth login (requires manual browser login)
3. **Daily Expiry** - Token expires every day at 7:30 AM and must be regenerated

This is why we recommend **skipping Kite integration** unless you specifically need portfolio features.

### Can I use this app for free?
**Yes!** The core stock analysis features are completely free:
- ✅ Yahoo Finance data (free)
- ✅ Technical analysis (free)
- ✅ Fundamental analysis (free)
- ✅ Google Gemini AI insights (free tier available)
- ✅ Multi-agent system (free)

Only optional: Zerodha Kite Connect (₹2000/month) for portfolio features.

### What features work WITHOUT Kite?
Everything except portfolio management:
- ✅ Stock search and analysis (via Stock Search Agent)
- ✅ Technical indicators (via Technical Analysis Agent)
- ✅ Fundamental metrics (via Fundamental Analysis Agent)
- ✅ AI-powered buy/sell recommendations (via AI Analysis Agent)
- ✅ Risk-reward calculations (via Risk Management Agent)
- ✅ Position sizing suggestions (via Risk Management Agent)
- ❌ Your Zerodha portfolio/holdings (requires Portfolio Agent + Kite)
- ❌ Order placement (requires Portfolio Agent + Kite)

## Troubleshooting

### Common Issues

1. **Agent Not Responding**
   - Check agent status at `/api/status`
   - Verify agent is registered in orchestrator
   - Check logs for agent errors

2. **MCP Server Errors**
   - Verify all agents are properly initialized
   - Check agent registration in orchestrator
   - Review MCP server logs

3. **Stock Data Not Loading**
   - Check internet connection
   - Verify stock symbol format (use NSE symbols without .NS)
   - Try alternative data sources (BSE symbols with .BO)

4. **AI Analysis Not Working**
   - Verify Gemini API key in `.env` file
   - Check API quota limits
   - Ensure proper internet connectivity

5. **Portfolio Data Empty**
   - Confirm Kite API connection
   - Check if you have active holdings/positions
   - Verify account permissions

## Security Considerations

1. **API Keys**: Never commit API keys to version control
2. **Access Tokens**: Kite access tokens expire daily - implement refresh mechanism
3. **HTTPS**: Use HTTPS in production for API security
4. **Rate Limits**: Respect API rate limits to avoid blocking
5. **Data Privacy**: Handle user financial data securely
6. **Agent Communication**: MCP server handles secure agent-to-agent communication

## Limitations

1. **Free Tier Restrictions**:
   - Gemini AI: Limited requests per day
   - Yahoo Finance: No real-time data guarantees
   - Technical indicators: Based on historical data

2. **Trading Restrictions**:
   - App provides suggestions only, not automated trading
   - Manual order placement required
   - Real-time data requires paid subscriptions

3. **Market Coverage**:
   - Primarily Indian stock markets (NSE/BSE)
   - Limited cryptocurrency support
   - No international markets

## Future Enhancements

- [ ] Real-time price streaming agent
- [ ] Advanced charting with candlestick patterns
- [ ] Options analysis agent
- [ ] Automated trading capabilities
- [ ] Mobile app development
- [ ] Multi-asset support (crypto, commodities)
- [ ] Social trading features
- [ ] Advanced backtesting engine
- [ ] Agent performance monitoring dashboard
- [ ] Distributed agent architecture

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This application is for educational and informational purposes only. It should not be considered as financial advice. Always consult with qualified financial advisors before making investment decisions. The developers are not responsible for any financial losses incurred from using this application.

Trading in stocks involves substantial risk of loss and is not suitable for all investors. Past performance is not indicative of future results.

## Support

For support and questions:
1. Check the troubleshooting section
2. Review API documentation:
   - [Kite Connect API](https://kite.trade/docs/)
   - [Google Gemini API](https://ai.google.dev/docs)
3. Create an issue on GitHub
4. Contact the development team

## Acknowledgments

- Zerodha for providing the Kite Connect API
- Google for the Gemini AI API
- Yahoo Finance for stock data
- TA-Lib community for technical analysis tools
- Bootstrap team for the UI framework
- MCP protocol community for agent communication patterns

---

**Happy Trading! 📈🤖**
