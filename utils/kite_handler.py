import os
from kiteconnect import KiteConnect
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta
import pandas as pd

load_dotenv()

class KiteHandler:
    """
    Zerodha Kite Connect Handler
    
    NOTE: Kite integration is OPTIONAL. The app works perfectly without it.
    Kite is only needed for:
    - Viewing your Zerodha portfolio/holdings
    - Placing orders programmatically
    - Real-time portfolio tracking
    
    Stock analysis features work WITHOUT Kite using free data sources (yfinance).
    
    To enable Kite (if you really need it):
    1. Get API Key & Secret from https://kite.zerodha.com/connect/login
    2. Run generate_access_token() to get access token (needs manual login)
    3. Add to .env file:
       KITE_API_KEY=your_key
       KITE_API_SECRET=your_secret
       KITE_ACCESS_TOKEN=your_token
    
    Note: Access token expires DAILY and requires regeneration.
    """
    
    def __init__(self):
        self.api_key = os.getenv('KITE_API_KEY')
        self.api_secret = os.getenv('KITE_API_SECRET')
        self.access_token = os.getenv('KITE_ACCESS_TOKEN')

        self.kite = None
        self._connected = False

        # Only try to connect if credentials are provided
        if not self.api_key or not self.access_token:
            return  # Silently skip - Kite is optional

        if self.api_key and self.access_token:
            try:
                self.kite = KiteConnect(api_key=self.api_key)
                self.kite.set_access_token(self.access_token)

                # Test connection
                profile = self.kite.profile()
                print(f"✓ Connected to Kite as: {profile['user_name']}")
                self._connected = True

            except Exception as e:
                print(f"⚠ Kite connection failed: {e}")
                print("  Continuing without Kite integration...")

    def is_connected(self):
        return self._connected and self.kite is not None

    def get_profile(self):
        if not self.is_connected():
            return None
        try:
            return self.kite.profile()
        except Exception as e:
            print(f"Error getting profile: {e}")
            return None

    def get_holdings(self):
        if not self.is_connected():
            return []
        try:
            return self.kite.holdings()
        except Exception as e:
            print(f"Error getting holdings: {e}")
            return []

    def get_positions(self):
        if not self.is_connected():
            return {'net': [], 'day': []}
        try:
            return self.kite.positions()
        except Exception as e:
            print(f"Error getting positions: {e}")
            return {'net': [], 'day': []}

    def get_funds(self):
        if not self.is_connected():
            return {'equity': {'available': {'cash': 0}}}
        try:
            return self.kite.margins()
        except Exception as e:
            print(f"Error getting funds: {e}")
            return {'equity': {'available': {'cash': 0}}}

    def get_instruments(self, exchange="NSE"):
        if not self.is_connected():
            return []
        try:
            return self.kite.instruments(exchange)
        except Exception as e:
            print(f"Error getting instruments: {e}")
            return []

    def get_quote(self, symbol):
        if not self.is_connected():
            return None
        try:
            return self.kite.quote(symbol)
        except Exception as e:
            print(f"Error getting quote for {symbol}: {e}")
            return None

    def get_historical_data(self, instrument_token, from_date, to_date, interval="day"):
        if not self.is_connected():
            return []
        try:
            return self.kite.historical_data(
                instrument_token=instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval=interval
            )
        except Exception as e:
            print(f"Error getting historical data: {e}")
            return []

    def place_order(self, tradingsymbol, exchange, transaction_type, quantity, 
                   order_type, product, price=None, trigger_price=None, 
                   stoploss=None, squareoff=None):
        if not self.is_connected():
            raise Exception("Not connected to Kite")

        try:
            order_params = {
                'tradingsymbol': tradingsymbol,
                'exchange': exchange,
                'transaction_type': transaction_type,
                'quantity': quantity,
                'order_type': order_type,
                'product': product
            }

            if price:
                order_params['price'] = price
            if trigger_price:
                order_params['trigger_price'] = trigger_price
            if stoploss:
                order_params['stoploss'] = stoploss
            if squareoff:
                order_params['squareoff'] = squareoff

            return self.kite.place_order(**order_params)

        except Exception as e:
            print(f"Error placing order: {e}")
            raise e

    def get_orders(self):
        if not self.is_connected():
            return []
        try:
            return self.kite.orders()
        except Exception as e:
            print(f"Error getting orders: {e}")
            return []

    def get_trades(self):
        if not self.is_connected():
            return []
        try:
            return self.kite.trades()
        except Exception as e:
            print(f"Error getting trades: {e}")
            return []

    @staticmethod
    def generate_access_token(api_key, api_secret):
        """
        Helper method to generate access token.
        This requires manual login through browser.
        
        Usage:
            python -c "from utils.kite_handler import KiteHandler; KiteHandler.generate_access_token('your_api_key', 'your_api_secret')"
        
        Steps:
        1. Opens browser for login
        2. After login, copy the full redirect URL
        3. Extract request_token from URL
        4. Use it to generate access token
        """
        kite = KiteConnect(api_key=api_key)
        
        # Generate login URL
        login_url = kite.login_url()
        print("\n" + "="*80)
        print("ZERODHA KITE ACCESS TOKEN GENERATOR")
        print("="*80)
        print(f"\n1. Open this URL in your browser:\n   {login_url}\n")
        print("2. Login with your Zerodha credentials")
        print("3. After successful login, you'll be redirected to a URL like:")
        print("   http://127.0.0.1/?request_token=XXXXX&action=login&status=success")
        print("\n4. Copy the ENTIRE redirect URL and paste it below:")
        print("="*80 + "\n")
        
        redirect_url = input("Paste the redirect URL here: ").strip()
        
        # Extract request token
        try:
            if 'request_token=' in redirect_url:
                request_token = redirect_url.split('request_token=')[1].split('&')[0]
            else:
                print("Error: Could not find request_token in URL")
                return
            
            # Generate access token
            data = kite.generate_session(request_token, api_secret=api_secret)
            access_token = data["access_token"]
            
            print("\n" + "="*80)
            print("SUCCESS! Access token generated:")
            print("="*80)
            print(f"\nAccess Token: {access_token}\n")
            print("Add this to your .env file:")
            print("-"*80)
            print(f"KITE_API_KEY={api_key}")
            print(f"KITE_API_SECRET={api_secret}")
            print(f"KITE_ACCESS_TOKEN={access_token}")
            print("-"*80)
            print("\nNote: This token expires daily at 7:30 AM and needs regeneration.")
            print("="*80 + "\n")
            
            return access_token
            
        except Exception as e:
            print(f"\nError generating access token: {e}")
            print("Make sure you copied the complete redirect URL.")
            return None