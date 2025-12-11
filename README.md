# Trading Analysis App

A comprehensive web application for analyzing Indian stocks using technical analysis, fundamental analysis, and AI-powered insights. Get buy/sell recommendations with 1:2 risk-reward ratio calculations using free data sources.

**✨ Works WITHOUT Zerodha Account** - Full stock analysis capabilities available without any broker integration!

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
- **Technical Analysis**: RSI, MACD, Bollinger Bands, Moving Averages, Support/Resistance levels
- **Fundamental Analysis**: P/E, P/B, ROE, Debt/Equity ratios, Revenue growth, Company financials
- **AI-Powered Insights**: Buy/sell recommendations using Google Gemini AI
- **Risk-Reward Calculations**: Automatic 1:2 risk-reward ratio analysis
- **Position Sizing**: Intelligent position size recommendations based on capital
- **Data Source**: Yahoo Finance (completely free!)

### 📊 Portfolio Management (Optional - Requires Zerodha Account)
- **Live Portfolio Sync**: Real-time sync with Zerodha Kite account
- **Holdings & Positions**: View current holdings and day trading positions
- **P&L Tracking**: Detailed profit/loss analysis
- **Sell Recommendations**: AI-powered suggestions on when to sell based on 1:2 risk-reward
- **Note**: Portfolio features are OPTIONAL. App works perfectly without them!

### 🚀 Technology Stack
- **Backend**: Python Flask
- **APIs**: Zerodha Kite Connect, Yahoo Finance, Google Gemini AI
- **Frontend**: Bootstrap 5, JavaScript, Chart.js
- **Analysis**: TA-Lib, Pandas, NumPy
- **Deployment**: Can be deployed on any cloud platform

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

### 1. Stock Analysis
1. Enter a stock symbol (e.g., RELIANCE, TCS, INFY)
2. Click "Analyze Stock"
3. View comprehensive analysis including:
   - Current price and AI recommendation
   - Technical indicators and signals
   - Fundamental ratios and company data
   - Risk-reward analysis with target and stop-loss prices
   - Position size recommendations

### 2. Portfolio Management
1. Navigate to "Portfolio" section
2. View your current holdings and positions
3. Check P&L for each stock
4. Get sell recommendations based on 1:2 risk-reward ratio
5. Analyze individual stocks directly from portfolio

### 3. Risk Management
The app automatically calculates:
- **Target Price**: Based on technical and fundamental analysis
- **Stop Loss**: Conservative stop-loss levels
- **Risk-Reward Ratio**: Ensures minimum 1:2 ratio
- **Position Size**: Based on available capital and risk tolerance
- **Breakeven Win Rate**: Required win rate for profitability

## API Endpoints

### Stock Analysis
- `POST /analyze` - Analyze a stock symbol
- `GET /api/status` - Check API connectivity status

### Portfolio Management
- `GET /portfolio` - View portfolio page
- `GET /sell-recommendations` - Get sell recommendations

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

## FAQ

### Do I need a Zerodha account to use this app?
**No!** The app works perfectly without Zerodha. All stock analysis features (technical analysis, fundamental analysis, AI recommendations) use free Yahoo Finance data. Zerodha is only needed if you want portfolio management features.

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

Only optional: Zerodha Kite Connect (₹2000/month) for portfolio features.

### What features work WITHOUT Kite?
Everything except portfolio management:
- ✅ Stock search and analysis
- ✅ Technical indicators (RSI, MACD, Bollinger Bands, etc.)
- ✅ Fundamental metrics (P/E, P/B, ROE, etc.)
- ✅ AI-powered buy/sell recommendations
- ✅ Risk-reward calculations
- ✅ Position sizing suggestions
- ❌ Your Zerodha portfolio/holdings (requires Kite)
- ❌ Order placement (requires Kite)

### How do I generate the Kite access token if I need it?
Use the built-in helper:
```bash
python -c "from utils.kite_handler import KiteHandler; KiteHandler.generate_access_token('your_api_key', 'your_api_secret')"
```
Follow the prompts to login via browser and generate the token.

### The app says "Kite not connected" - is this a problem?
**No, this is normal!** The app is designed to work without Kite. This message just means portfolio features are disabled, but all analysis features are working fine.

## Troubleshooting

### Common Issues

1. **Kite API Connection Failed (If using Kite)**
   - This is OPTIONAL - app works fine without Kite
   - If you need it: Verify API credentials in `.env` file
   - Ensure access token is valid (regenerate if expired)
   - Check if Kite Connect subscription is active (₹2000/month)

2. **Stock Data Not Loading**
   - Check internet connection
   - Verify stock symbol format (use NSE symbols without .NS)
   - Try alternative data sources (BSE symbols with .BO)

3. **AI Analysis Not Working**
   - Verify Gemini API key in `.env` file
   - Check API quota limits
   - Ensure proper internet connectivity

4. **Portfolio Data Empty**
   - Confirm Kite API connection
   - Check if you have active holdings/positions
   - Verify account permissions

### Error Logs
Check console logs for detailed error messages:
```bash
# In development mode, errors are displayed in terminal
python app.py

# For production, check application logs
tail -f /var/log/trading_app.log
```

## Security Considerations

1. **API Keys**: Never commit API keys to version control
2. **Access Tokens**: Kite access tokens expire daily - implement refresh mechanism
3. **HTTPS**: Use HTTPS in production for API security
4. **Rate Limits**: Respect API rate limits to avoid blocking
5. **Data Privacy**: Handle user financial data securely

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

- [ ] Real-time price streaming
- [ ] Advanced charting with candlestick patterns
- [ ] Options analysis and strategies
- [ ] Automated trading capabilities
- [ ] Mobile app development
- [ ] Multi-asset support (crypto, commodities)
- [ ] Social trading features
- [ ] Advanced backtesting engine

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

---

**Happy Trading! 📈**