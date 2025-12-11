import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import json

class FundamentalAnalyzer:
    def __init__(self):
        self.data_cache = {}

    def get_stock_data(self, symbol, period="1y"):
        """Get stock data with proper NSE suffix"""
        original_symbol = symbol
        try:
            # Add .NS suffix for NSE stocks if not present
            if not symbol.endswith('.NS') and not symbol.endswith('.BO'):
                symbol = f"{symbol}.NS"

            # Check cache first
            cache_key = f"{symbol}_{period}"
            if cache_key in self.data_cache:
                cache_time, data = self.data_cache[cache_key]
                if datetime.now() - cache_time < timedelta(hours=1) and not data.empty:
                    return data

            # Try fetching with timeout
            stock = yf.Ticker(symbol)
            try:
                data = stock.history(period=period, timeout=10)
            except Exception as e:
                print(f"Error fetching {symbol} with period {period}: {e}")
                data = pd.DataFrame()

            if data.empty:
                # Try BSE if NSE fails
                if symbol.endswith('.NS'):
                    bse_symbol = symbol.replace('.NS', '.BO')
                    print(f"Trying BSE symbol: {bse_symbol}")
                    stock = yf.Ticker(bse_symbol)
                    try:
                        data = stock.history(period=period, timeout=10)
                    except Exception as e:
                        print(f"Error fetching BSE data for {bse_symbol}: {e}")
                        data = pd.DataFrame()

            # If still empty, try shorter period
            if data.empty and period == "1y":
                print(f"Trying shorter period (1mo) for {symbol}")
                try:
                    data = stock.history(period="1mo", timeout=10)
                except Exception as e:
                    print(f"Error fetching with 1mo period: {e}")

            # Cache the data only if we got some
            if not data.empty:
                self.data_cache[cache_key] = (datetime.now(), data)
            
            return data

        except Exception as e:
            print(f"Error fetching data for {original_symbol}: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

    def get_company_info(self, symbol):
        """Get company fundamental information"""
        try:
            if not symbol.endswith('.NS') and not symbol.endswith('.BO'):
                symbol = f"{symbol}.NS"

            stock = yf.Ticker(symbol)
            info = stock.info

            if not info or 'symbol' not in info:
                # Try BSE if NSE fails
                symbol = symbol.replace('.NS', '.BO')
                stock = yf.Ticker(symbol)
                info = stock.info

            return info

        except Exception as e:
            print(f"Error getting company info for {symbol}: {e}")
            return {}

    def calculate_financial_ratios(self, info):
        """Calculate key financial ratios"""
        ratios = {}

        try:
            # P/E Ratio
            ratios['pe_ratio'] = info.get('trailingPE', info.get('forwardPE', None))

            # P/B Ratio
            ratios['pb_ratio'] = info.get('priceToBook', None)

            # Debt to Equity
            total_debt = info.get('totalDebt', 0)
            total_equity = info.get('totalStockholderEquity', 1)
            ratios['debt_to_equity'] = total_debt / total_equity if total_equity != 0 else None

            # ROE (Return on Equity)
            ratios['roe'] = info.get('returnOnEquity', None)

            # ROA (Return on Assets)
            ratios['roa'] = info.get('returnOnAssets', None)

            # Current Ratio
            current_assets = info.get('totalCurrentAssets', 0)
            current_liabilities = info.get('totalCurrentLiabilities', 1)
            ratios['current_ratio'] = current_assets / current_liabilities if current_liabilities != 0 else None

            # Profit Margin
            ratios['profit_margin'] = info.get('profitMargins', None)

            # Revenue Growth
            ratios['revenue_growth'] = info.get('revenueGrowth', None)

            # Earnings Growth
            ratios['earnings_growth'] = info.get('earningsGrowth', None)

        except Exception as e:
            print(f"Error calculating ratios: {e}")

        return ratios

    def get_financial_statements(self, symbol):
        """Get basic financial statement data"""
        try:
            if not symbol.endswith('.NS') and not symbol.endswith('.BO'):
                symbol = f"{symbol}.NS"

            stock = yf.Ticker(symbol)

            # Get financials
            financials = stock.financials
            balance_sheet = stock.balance_sheet
            cashflow = stock.cashflow

            if financials.empty:
                # Try BSE
                symbol = symbol.replace('.NS', '.BO')
                stock = yf.Ticker(symbol)
                financials = stock.financials
                balance_sheet = stock.balance_sheet
                cashflow = stock.cashflow

            return {
                'income_statement': financials.to_dict() if not financials.empty else {},
                'balance_sheet': balance_sheet.to_dict() if not balance_sheet.empty else {},
                'cash_flow': cashflow.to_dict() if not cashflow.empty else {}
            }

        except Exception as e:
            print(f"Error getting financial statements: {e}")
            return {'income_statement': {}, 'balance_sheet': {}, 'cash_flow': {}}

    def analyze_price_trends(self, data, symbol):
        """Analyze price trends and patterns"""
        if data.empty:
            return {}

        try:
            current_price = data['Close'].iloc[-1]

            # Price changes
            price_changes = {
                '1_day': ((data['Close'].iloc[-1] / data['Close'].iloc[-2]) - 1) * 100 if len(data) >= 2 else 0,
                '1_week': ((data['Close'].iloc[-1] / data['Close'].iloc[-5]) - 1) * 100 if len(data) >= 5 else 0,
                '1_month': ((data['Close'].iloc[-1] / data['Close'].iloc[-21]) - 1) * 100 if len(data) >= 21 else 0,
                '3_month': ((data['Close'].iloc[-1] / data['Close'].iloc[-63]) - 1) * 100 if len(data) >= 63 else 0,
                '1_year': ((data['Close'].iloc[-1] / data['Close'].iloc[0]) - 1) * 100 if len(data) >= 252 else 0
            }

            # 52-week high/low
            high_52w = data['High'].max()
            low_52w = data['Low'].min()

            # Average volume
            avg_volume = data['Volume'].mean()
            recent_volume = data['Volume'].iloc[-5:].mean()  # Last 5 days average

            return {
                'current_price': current_price,
                'price_changes': price_changes,
                '52_week_high': high_52w,
                '52_week_low': low_52w,
                'distance_from_52w_high': ((current_price / high_52w) - 1) * 100,
                'distance_from_52w_low': ((current_price / low_52w) - 1) * 100,
                'average_volume': avg_volume,
                'recent_volume': recent_volume,
                'volume_trend': 'Above Average' if recent_volume > avg_volume else 'Below Average'
            }

        except Exception as e:
            print(f"Error analyzing price trends: {e}")
            return {}

    def get_sector_industry_info(self, info):
        """Extract sector and industry information"""
        return {
            'sector': info.get('sector', 'Unknown'),
            'industry': info.get('industry', 'Unknown'),
            'market_cap': info.get('marketCap', None),
            'enterprise_value': info.get('enterpriseValue', None),
            'employees': info.get('fullTimeEmployees', None)
        }

    def calculate_intrinsic_value_estimate(self, info, ratios):
        """Simple intrinsic value estimation using P/E and growth"""
        try:
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            pe_ratio = ratios.get('pe_ratio', None)
            earnings_growth = ratios.get('earnings_growth', None)

            if not current_price or not pe_ratio or not earnings_growth:
                return None

            # Simple PEG-based valuation
            if earnings_growth > 0:
                fair_pe = earnings_growth * 100  # Very simplified
                estimated_fair_value = (current_price / pe_ratio) * fair_pe

                return {
                    'estimated_fair_value': estimated_fair_value,
                    'current_price': current_price,
                    'upside_downside': ((estimated_fair_value / current_price) - 1) * 100,
                    'method': 'Simplified PEG-based estimation'
                }

            return None

        except Exception as e:
            print(f"Error calculating intrinsic value: {e}")
            return None

    def analyze(self, symbol):
        """Complete fundamental analysis"""
        try:
            # Get company information
            info = self.get_company_info(symbol)
            if not info:
                return {'error': 'Could not fetch company information'}

            # Get stock price data
            data = self.get_stock_data(symbol)

            # Calculate ratios
            ratios = self.calculate_financial_ratios(info)

            # Analyze price trends
            price_analysis = self.analyze_price_trends(data, symbol)

            # Get sector/industry info
            sector_info = self.get_sector_industry_info(info)

            # Get financial statements
            statements = self.get_financial_statements(symbol)

            # Estimate intrinsic value
            intrinsic_value = self.calculate_intrinsic_value_estimate(info, ratios)

            # Generate fundamental score
            score = self.calculate_fundamental_score(ratios, info)

            return {
                'company_name': info.get('longName', symbol),
                'symbol': symbol,
                'sector_info': sector_info,
                'financial_ratios': ratios,
                'price_analysis': price_analysis,
                'intrinsic_value_estimate': intrinsic_value,
                'fundamental_score': score,
                'key_stats': {
                    'beta': info.get('beta', None),
                    'dividend_yield': info.get('dividendYield', None),
                    'payout_ratio': info.get('payoutRatio', None),
                    'book_value': info.get('bookValue', None)
                },
                'financial_statements_available': {
                    'income_statement': bool(statements['income_statement']),
                    'balance_sheet': bool(statements['balance_sheet']),
                    'cash_flow': bool(statements['cash_flow'])
                },
                'analysis_timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {'error': f'Fundamental analysis failed: {str(e)}'}

    def calculate_fundamental_score(self, ratios, info):
        """Calculate a simple fundamental strength score (0-100)"""
        score = 50  # Start with neutral score

        try:
            # P/E ratio scoring
            pe = ratios.get('pe_ratio')
            if pe:
                if 10 <= pe <= 20:
                    score += 10
                elif 20 < pe <= 30:
                    score += 5
                elif pe > 40:
                    score -= 10

            # ROE scoring
            roe = ratios.get('roe')
            if roe:
                if roe > 0.15:  # 15%+
                    score += 15
                elif roe > 0.10:  # 10-15%
                    score += 10
                elif roe < 0:
                    score -= 15

            # Debt to Equity scoring
            de = ratios.get('debt_to_equity')
            if de is not None:
                if de < 0.3:
                    score += 10
                elif de > 1.0:
                    score -= 10

            # Revenue growth scoring
            rev_growth = ratios.get('revenue_growth')
            if rev_growth:
                if rev_growth > 0.15:  # 15%+
                    score += 10
                elif rev_growth > 0.05:  # 5-15%
                    score += 5
                elif rev_growth < 0:
                    score -= 10

            # Current ratio scoring
            cr = ratios.get('current_ratio')
            if cr:
                if 1.5 <= cr <= 3.0:
                    score += 5
                elif cr < 1.0:
                    score -= 10

            # Ensure score is between 0 and 100
            score = max(0, min(100, score))

            return {
                'score': score,
                'rating': 'Strong' if score >= 70 else 'Moderate' if score >= 50 else 'Weak',
                'factors_considered': ['P/E Ratio', 'ROE', 'Debt/Equity', 'Revenue Growth', 'Current Ratio']
            }

        except Exception as e:
            print(f"Error calculating fundamental score: {e}")
            return {'score': 50, 'rating': 'Unknown', 'factors_considered': []}