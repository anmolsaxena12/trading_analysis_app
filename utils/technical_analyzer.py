import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import MACD, EMAIndicator, SMAIndicator
from ta.volatility import BollingerBands
import yfinance as yf
from datetime import datetime, timedelta

class TechnicalAnalyzer:
    def __init__(self):
        self.indicators = {}

    def get_stock_data(self, symbol, period="1y"):
        """Get stock data with proper NSE suffix"""
        try:
            # Add .NS suffix for NSE stocks if not present
            if not symbol.endswith('.NS') and not symbol.endswith('.BO'):
                symbol = f"{symbol}.NS"

            stock = yf.Ticker(symbol)
            try:
                data = stock.history(period=period, timeout=10)
            except Exception as e:
                print(f"Error fetching {symbol}: {e}")
                data = pd.DataFrame()

            if data.empty:
                # Try BSE if NSE fails
                if symbol.endswith('.NS'):
                    symbol = symbol.replace('.NS', '.BO')
                    stock = yf.Ticker(symbol)
                    try:
                        data = stock.history(period=period, timeout=10)
                    except Exception as e:
                        print(f"Error fetching BSE data: {e}")
                        data = pd.DataFrame()

            # If still empty, try shorter period
            if data.empty and period == "1y":
                try:
                    data = stock.history(period="1mo", timeout=10)
                except Exception as e:
                    print(f"Error fetching with shorter period: {e}")

            return data
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

    def calculate_rsi(self, data, period=14):
        """Calculate RSI"""
        rsi_indicator = RSIIndicator(close=data['Close'], window=period)
        rsi_values = rsi_indicator.rsi()
        return rsi_values.values if hasattr(rsi_values, 'values') else rsi_values

    def calculate_macd(self, data, fastperiod=12, slowperiod=26, signalperiod=9):
        """Calculate MACD"""
        macd_indicator = MACD(close=data['Close'], window_fast=fastperiod, window_slow=slowperiod, window_sign=signalperiod)
        macd = macd_indicator.macd()
        macd_signal = macd_indicator.macd_signal()
        macd_hist = macd_indicator.macd_diff()
        return (macd.values if hasattr(macd, 'values') else macd,
                macd_signal.values if hasattr(macd_signal, 'values') else macd_signal,
                macd_hist.values if hasattr(macd_hist, 'values') else macd_hist)

    def calculate_bollinger_bands(self, data, period=20, std=2):
        """Calculate Bollinger Bands"""
        bb_indicator = BollingerBands(close=data['Close'], window=period, window_dev=std)
        upper = bb_indicator.bollinger_hband()
        middle = bb_indicator.bollinger_mavg()
        lower = bb_indicator.bollinger_lband()
        return (upper.values if hasattr(upper, 'values') else upper,
                middle.values if hasattr(middle, 'values') else middle,
                lower.values if hasattr(lower, 'values') else lower)

    def calculate_moving_averages(self, data):
        """Calculate various moving averages"""
        close = data['Close']
        return {
            'SMA_10': SMAIndicator(close=close, window=10).sma_indicator().values,
            'SMA_20': SMAIndicator(close=close, window=20).sma_indicator().values,
            'SMA_50': SMAIndicator(close=close, window=50).sma_indicator().values,
            'SMA_200': SMAIndicator(close=close, window=200).sma_indicator().values,
            'EMA_10': EMAIndicator(close=close, window=10).ema_indicator().values,
            'EMA_20': EMAIndicator(close=close, window=20).ema_indicator().values,
            'EMA_50': EMAIndicator(close=close, window=50).ema_indicator().values
        }

    def calculate_stochastic(self, data, k_period=14, d_period=3):
        """Calculate Stochastic Oscillator"""
        stoch_indicator = StochasticOscillator(high=data['High'], low=data['Low'], close=data['Close'], 
                                                window=k_period, smooth_window=d_period)
        slowk = stoch_indicator.stoch()
        slowd = stoch_indicator.stoch_signal()
        return (slowk.values if hasattr(slowk, 'values') else slowk,
                slowd.values if hasattr(slowd, 'values') else slowd)

    def calculate_support_resistance(self, data, window=20):
        """Calculate support and resistance levels"""
        highs = data['High'].rolling(window=window).max()
        lows = data['Low'].rolling(window=window).min()

        # Find recent support and resistance
        recent_high = highs.iloc[-1]
        recent_low = lows.iloc[-1]

        return {
            'resistance': recent_high,
            'support': recent_low,
            'current_price': data['Close'].iloc[-1]
        }

    def generate_signals(self, data):
        """Generate buy/sell signals based on technical indicators"""
        signals = {}

        # RSI signals
        rsi = self.calculate_rsi(data)
        current_rsi = rsi[-1] if len(rsi) > 0 else 50

        if current_rsi < 30:
            signals['rsi_signal'] = 'BUY'
            signals['rsi_strength'] = 'Strong'
        elif current_rsi > 70:
            signals['rsi_signal'] = 'SELL'
            signals['rsi_strength'] = 'Strong'
        else:
            signals['rsi_signal'] = 'HOLD'
            signals['rsi_strength'] = 'Weak'

        # MACD signals
        macd, signal, histogram = self.calculate_macd(data)
        if len(macd) > 1 and len(signal) > 1:
            if macd[-1] > signal[-1] and macd[-2] <= signal[-2]:
                signals['macd_signal'] = 'BUY'
            elif macd[-1] < signal[-1] and macd[-2] >= signal[-2]:
                signals['macd_signal'] = 'SELL'
            else:
                signals['macd_signal'] = 'HOLD'
        else:
            signals['macd_signal'] = 'HOLD'

        # Moving Average signals
        mas = self.calculate_moving_averages(data)
        current_price = data['Close'].iloc[-1]

        above_sma20 = current_price > mas['SMA_20'][-1] if len(mas['SMA_20']) > 0 else False
        above_sma50 = current_price > mas['SMA_50'][-1] if len(mas['SMA_50']) > 0 else False

        if above_sma20 and above_sma50:
            signals['trend_signal'] = 'BUY'
        elif not above_sma20 and not above_sma50:
            signals['trend_signal'] = 'SELL'
        else:
            signals['trend_signal'] = 'HOLD'

        # Bollinger Bands signals
        upper, middle, lower = self.calculate_bollinger_bands(data)
        if len(upper) > 0 and len(lower) > 0:
            if current_price <= lower[-1]:
                signals['bb_signal'] = 'BUY'
            elif current_price >= upper[-1]:
                signals['bb_signal'] = 'SELL'
            else:
                signals['bb_signal'] = 'HOLD'
        else:
            signals['bb_signal'] = 'HOLD'

        return signals

    def calculate_volatility(self, data, period=20):
        """Calculate price volatility"""
        returns = data['Close'].pct_change()
        volatility = returns.rolling(window=period).std() * np.sqrt(252)  # Annualized
        return volatility.iloc[-1] if len(volatility) > 0 else 0

    def analyze(self, data):
        """Complete technical analysis"""
        if data.empty:
            return {'error': 'No data available for analysis'}

        try:
            # Calculate all indicators
            rsi = self.calculate_rsi(data)
            macd, macd_signal, macd_histogram = self.calculate_macd(data)
            bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(data)
            mas = self.calculate_moving_averages(data)
            stoch_k, stoch_d = self.calculate_stochastic(data)
            support_resistance = self.calculate_support_resistance(data)
            signals = self.generate_signals(data)
            volatility = self.calculate_volatility(data)

            current_price = data['Close'].iloc[-1]

            # Overall sentiment
            buy_signals = sum([1 for signal in signals.values() if signal == 'BUY'])
            sell_signals = sum([1 for signal in signals.values() if signal == 'SELL'])

            if buy_signals > sell_signals:
                overall_sentiment = 'BULLISH'
            elif sell_signals > buy_signals:
                overall_sentiment = 'BEARISH'
            else:
                overall_sentiment = 'NEUTRAL'

            return {
                'current_price': current_price,
                'rsi': rsi[-1] if len(rsi) > 0 else None,
                'macd': {
                    'macd': macd[-1] if len(macd) > 0 else None,
                    'signal': macd_signal[-1] if len(macd_signal) > 0 else None,
                    'histogram': macd_histogram[-1] if len(macd_histogram) > 0 else None
                },
                'bollinger_bands': {
                    'upper': bb_upper[-1] if len(bb_upper) > 0 else None,
                    'middle': bb_middle[-1] if len(bb_middle) > 0 else None,
                    'lower': bb_lower[-1] if len(bb_lower) > 0 else None
                },
                'moving_averages': {k: v[-1] if len(v) > 0 else None for k, v in mas.items()},
                'stochastic': {
                    'k': stoch_k[-1] if len(stoch_k) > 0 else None,
                    'd': stoch_d[-1] if len(stoch_d) > 0 else None
                },
                'support_resistance': support_resistance,
                'volatility': volatility,
                'signals': signals,
                'overall_sentiment': overall_sentiment,
                'analysis_timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {'error': f'Technical analysis failed: {str(e)}'}