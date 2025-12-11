"""
Stock Scanner for Swing Trading Recommendations
Scans multiple stocks and filters for good technical and fundamental opportunities
"""
from datetime import datetime, timedelta
import traceback

class StockScanner:
    def __init__(self, technical_analyzer, fundamental_analyzer, ai_analyzer, risk_manager):
        self.technical_analyzer = technical_analyzer
        self.fundamental_analyzer = fundamental_analyzer
        self.ai_analyzer = ai_analyzer
        self.risk_manager = risk_manager
        
        # Popular Indian stocks for scanning
        self.default_stocks = [
            'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR', 'ICICIBANK',
            'BHARTIARTL', 'SBIN', 'BAJFINANCE', 'LICI', 'ITC', 'SUNPHARMA',
            'HCLTECH', 'AXISBANK', 'KOTAKBANK', 'LT', 'ASIANPAINT', 'MARUTI',
            'TITAN', 'ULTRACEMCO', 'NESTLEIND', 'WIPRO', 'ONGC', 'NTPC',
            'POWERGRID', 'TECHM', 'ADANIENT', 'JSWSTEEL', 'TATAMOTORS', 'TATASTEEL'
        ]
    
    def scan_stocks(self, symbols=None, min_score=60, max_results=20):
        """
        Scan stocks and return buy recommendations
        
        Args:
            symbols: List of stock symbols to scan (default: popular stocks)
            min_score: Minimum overall score to include (0-100)
            max_results: Maximum number of recommendations to return
        
        Returns:
            List of recommendation dictionaries
        """
        if symbols is None:
            symbols = self.default_stocks
        
        recommendations = []
        
        print(f"Scanning {len(symbols)} stocks for swing trading opportunities...")
        
        for i, symbol in enumerate(symbols, 1):
            try:
                print(f"[{i}/{len(symbols)}] Analyzing {symbol}...")
                
                # Get stock data
                stock_data = self.fundamental_analyzer.get_stock_data(symbol)
                if stock_data.empty:
                    continue
                
                current_price = stock_data['Close'].iloc[-1]
                
                # Technical Analysis
                technical_signals = self.technical_analyzer.analyze(stock_data)
                if technical_signals.get('error'):
                    continue
                
                # Fundamental Analysis
                fundamental_data = self.fundamental_analyzer.analyze(symbol)
                if fundamental_data.get('error'):
                    continue
                
                # AI Analysis
                buying_analysis = self.ai_analyzer.analyze_buying_opportunity(
                    symbol, current_price, technical_signals, fundamental_data
                )
                
                # Calculate overall score
                overall_score = self._calculate_overall_score(
                    technical_signals, fundamental_data, buying_analysis
                )
                
                # Include if meets minimum score (relaxed criteria for swing trading)
                # Use score-based filtering - don't require should_buy=True
                if overall_score >= min_score:
                    # Calculate risk-reward with reasonable defaults
                    target_price = buying_analysis.get('target_price', current_price * 1.1)
                    stop_loss = buying_analysis.get('stop_loss', current_price * 0.95)
                    
                    # Ensure reasonable targets if not provided or invalid
                    if target_price <= current_price:
                        target_price = current_price * 1.1  # 10% target
                    if stop_loss >= current_price:
                        stop_loss = current_price * 0.95  # 5% stop loss
                    
                    # Always calculate risk-reward (even if not perfect)
                    risk_reward = self.risk_manager.calculate_risk_reward(
                        current_price, target_price, stop_loss
                    )
                    
                    # If risk_reward calculation failed, create a basic one
                    if not risk_reward:
                        risk = abs(current_price - stop_loss)
                        reward = abs(target_price - current_price)
                        ratio = reward / risk if risk > 0 else 1.0
                        risk_reward = {
                            'entry_price': float(current_price),
                            'target_price': float(target_price),
                            'stop_loss_price': float(stop_loss),
                            'risk_amount': float(risk),
                            'reward_amount': float(reward),
                            'risk_reward_ratio': float(ratio),
                            'ratio_formatted': f"1:{ratio:.2f}",
                            'breakeven_win_rate': float((1 / (1 + ratio)) * 100),
                            'is_favorable': bool(ratio >= 2.0),
                            'recommendation': 'Moderate risk-reward' if ratio >= 1.5 else 'Below ideal'
                        }
                    
                    # Accept all recommendations that meet score threshold
                    # (Don't filter by is_favorable - show all with risk-reward info)
                    # Calculate timeline (swing trading typically 1-4 weeks)
                    timeline = self._calculate_timeline(
                        technical_signals, fundamental_data, buying_analysis
                    )
                    
                    recommendation = {
                        'symbol': symbol,
                        'company_name': fundamental_data.get('company_name', symbol),
                        'current_price': float(current_price),
                        'buy_price': float(current_price),  # Entry price
                        'target_price': float(target_price),  # Sell price
                        'stop_loss': float(stop_loss),
                        'risk_reward': risk_reward,
                        'overall_score': float(overall_score),
                        'technical_score': float(self._calculate_technical_score(technical_signals)),
                        'fundamental_score': float(fundamental_data.get('fundamental_score', {}).get('score', 50)),
                        'ai_score': float(buying_analysis.get('overall_score', 50)),
                        'confidence': buying_analysis.get('confidence_level', 'Medium'),
                        'timeline': timeline,
                        'key_reasons': buying_analysis.get('key_reasons', [])[:3],
                        'risks': buying_analysis.get('risks', [])[:2],
                        'sector': fundamental_data.get('sector_info', {}).get('sector', 'Unknown'),
                        'technical_signals': {
                            'rsi': float(technical_signals.get('rsi')) if technical_signals.get('rsi') is not None else None,
                            'macd_signal': technical_signals.get('signals', {}).get('macd_signal'),
                            'trend_signal': technical_signals.get('signals', {}).get('trend_signal'),
                            'overall_sentiment': technical_signals.get('overall_sentiment')
                        },
                        'potential_profit_percent': float(((target_price - current_price) / current_price) * 100),
                        'risk_percent': float(((current_price - stop_loss) / current_price) * 100),
                        'scanned_at': datetime.now().isoformat()
                    }
                    
                    recommendations.append(recommendation)
                    print(f"  ✓ {symbol} added (Score: {overall_score:.1f}, R:R={risk_reward.get('ratio_formatted', 'N/A')}, should_buy={buying_analysis.get('should_buy', False)})")
                
            except Exception as e:
                print(f"  ✗ Error analyzing {symbol}: {str(e)}")
                traceback.print_exc()
                continue
        
        # Sort by overall score (descending)
        recommendations.sort(key=lambda x: x['overall_score'], reverse=True)
        
        # Limit results
        recommendations = recommendations[:max_results]
        
        print(f"\n✓ Scan complete: {len(recommendations)} recommendations found")
        
        return recommendations
    
    def _calculate_overall_score(self, technical_signals, fundamental_data, buying_analysis):
        """Calculate overall recommendation score (0-100)"""
        try:
            # Technical score (0-40 points)
            tech_score = self._calculate_technical_score(technical_signals)
            technical_weighted = (tech_score / 100) * 40
            
            # Fundamental score (0-30 points)
            fund_score = fundamental_data.get('fundamental_score', {}).get('score', 50)
            fundamental_weighted = (fund_score / 100) * 30
            
            # AI score (0-30 points)
            ai_score = buying_analysis.get('overall_score', 50)
            ai_weighted = (ai_score / 100) * 30
            
            overall = technical_weighted + fundamental_weighted + ai_weighted
            
            return min(100, max(0, overall))
        except:
            return 50
    
    def _calculate_technical_score(self, technical_signals):
        """Calculate technical analysis score (0-100)"""
        try:
            score = 50  # Base score
            
            # RSI scoring
            rsi = technical_signals.get('rsi')
            if rsi:
                if 30 <= rsi <= 70:
                    score += 10
                elif rsi < 30:
                    score += 15  # Oversold - good entry
                elif rsi > 70:
                    score -= 10  # Overbought
            
            # Signal scoring
            signals = technical_signals.get('signals', {})
            buy_signals = sum(1 for s in signals.values() if s == 'BUY')
            sell_signals = sum(1 for s in signals.values() if s == 'SELL')
            
            score += (buy_signals - sell_signals) * 5
            
            # Sentiment scoring
            sentiment = technical_signals.get('overall_sentiment', 'NEUTRAL')
            if sentiment == 'BULLISH':
                score += 10
            elif sentiment == 'BEARISH':
                score -= 10
            
            return min(100, max(0, score))
        except:
            return 50
    
    def _calculate_timeline(self, technical_signals, fundamental_data, buying_analysis):
        """Calculate expected timeline for swing trade"""
        try:
            time_horizon = buying_analysis.get('time_horizon', 'Medium term')
            
            # Map time horizon to days
            if 'Short' in time_horizon:
                days = 7  # 1 week
            elif 'Medium' in time_horizon:
                days = 21  # 3 weeks
            elif 'Long' in time_horizon:
                days = 60  # 2 months
            else:
                days = 21  # Default 3 weeks
            
            # Adjust based on technical indicators
            volatility = technical_signals.get('volatility', 0)
            if volatility and volatility > 0.3:  # High volatility
                days = max(7, days - 7)  # Shorter timeline
            elif volatility and volatility < 0.15:  # Low volatility
                days = min(60, days + 7)  # Longer timeline
            
            buy_date = datetime.now()
            sell_date = buy_date + timedelta(days=days)
            
            return {
                'buy_date': buy_date.strftime('%Y-%m-%d'),
                'expected_sell_date': sell_date.strftime('%Y-%m-%d'),
                'days_holding': days,
                'time_horizon': time_horizon
            }
        except:
            # Default timeline
            buy_date = datetime.now()
            sell_date = buy_date + timedelta(days=21)
            return {
                'buy_date': buy_date.strftime('%Y-%m-%d'),
                'expected_sell_date': sell_date.strftime('%Y-%m-%d'),
                'days_holding': 21,
                'time_horizon': 'Medium term'
            }

