import os
import google.generativeai as genai
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

class AIAnalyzer:
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        self._available = False

        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                # Try different model names (with and without 'models/' prefix)
                model_names = [
                    'models/gemini-2.5-pro',
                    'models/gemini-2.0-flash',
                    'models/gemini-2.5-flash',
                    'gemini-pro',
                    'gemini-1.5-pro',
                    'gemini-1.5-flash'
                ]
                self.model = None
                for model_name in model_names:
                    try:
                        self.model = genai.GenerativeModel(model_name)
                        print(f"Using AI model: {model_name}")
                        break
                    except Exception as e:
                        continue
                
                # If still no model, try listing available models
                if not self.model:
                    try:
                        models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                        if models:
                            # Prefer models with 'pro' in name
                            pro_models = [m for m in models if 'pro' in m.name.lower() and 'preview' not in m.name.lower()]
                            if pro_models:
                                self.model = genai.GenerativeModel(pro_models[0].name)
                                print(f"Using AI model: {pro_models[0].name}")
                            else:
                                # Use flash models as fallback
                                flash_models = [m for m in models if 'flash' in m.name.lower()]
                                if flash_models:
                                    self.model = genai.GenerativeModel(flash_models[0].name)
                                    print(f"Using AI model: {flash_models[0].name}")
                                else:
                                    self.model = genai.GenerativeModel(models[0].name)
                                    print(f"Using AI model: {models[0].name}")
                    except Exception as e:
                        print(f"Error listing models: {e}")
                        pass
                
                if self.model:
                    self._available = True
                    print("Gemini AI initialized successfully")
                else:
                    print("Could not initialize any Gemini model, will use fallback analysis")
            except Exception as e:
                print(f"Gemini AI initialization failed: {e}")
        else:
            print("Gemini API key not found. AI analysis will not be available.")

    def is_available(self):
        return self._available

    def analyze_buying_opportunity(self, symbol, current_price, technical_signals, fundamental_data):
        """Analyze if it's a good time to buy using AI"""
        if not self._available:
            return self._fallback_analysis(current_price, technical_signals, fundamental_data)

        try:
            prompt = self._create_analysis_prompt(symbol, current_price, technical_signals, fundamental_data)

            response = self.model.generate_content(prompt)
            ai_response = response.text

            # Parse AI response and combine with rule-based analysis
            analysis = self._parse_ai_response(ai_response, current_price)

            # Add rule-based validation
            rule_based = self._fallback_analysis(current_price, technical_signals, fundamental_data)
            analysis.update({
                'ai_available': True,
                'ai_response': ai_response,
                'rule_based_validation': rule_based
            })

            return analysis

        except Exception as e:
            print(f"AI analysis error: {e}")
            # Fallback to rule-based analysis
            return self._fallback_analysis(current_price, technical_signals, fundamental_data)

    def _create_analysis_prompt(self, symbol, current_price, technical_signals, fundamental_data):
        """Create a comprehensive prompt for AI analysis"""

        prompt = f"""
        As a professional stock market analyst, analyze the following stock for buying opportunity:

        Stock: {symbol}
        Current Price: ₹{current_price:.2f}

        TECHNICAL ANALYSIS:
        - Overall Sentiment: {technical_signals.get('overall_sentiment', 'Unknown')}
        - RSI: {technical_signals.get('rsi', 'N/A')} (Signal: {technical_signals.get('signals', {}).get('rsi_signal', 'N/A')})
        - MACD Signal: {technical_signals.get('signals', {}).get('macd_signal', 'N/A')}
        - Trend Signal: {technical_signals.get('signals', {}).get('trend_signal', 'N/A')}
        - Bollinger Bands Signal: {technical_signals.get('signals', {}).get('bb_signal', 'N/A')}
        - Support Level: ₹{technical_signals.get('support_resistance', {}).get('support', 'N/A')}
        - Resistance Level: ₹{technical_signals.get('support_resistance', {}).get('resistance', 'N/A')}
        - Volatility: {technical_signals.get('volatility', 'N/A')}

        FUNDAMENTAL ANALYSIS:
        - Company: {fundamental_data.get('company_name', symbol)}
        - Sector: {fundamental_data.get('sector_info', {}).get('sector', 'Unknown')}
        - P/E Ratio: {fundamental_data.get('financial_ratios', {}).get('pe_ratio', 'N/A')}
        - P/B Ratio: {fundamental_data.get('financial_ratios', {}).get('pb_ratio', 'N/A')}
        - ROE: {fundamental_data.get('financial_ratios', {}).get('roe', 'N/A')}
        - Debt/Equity: {fundamental_data.get('financial_ratios', {}).get('debt_to_equity', 'N/A')}
        - Revenue Growth: {fundamental_data.get('financial_ratios', {}).get('revenue_growth', 'N/A')}
        - Fundamental Score: {fundamental_data.get('fundamental_score', {}).get('score', 'N/A')}/100
        - 52W High: ₹{fundamental_data.get('price_analysis', {}).get('52_week_high', 'N/A')}
        - 52W Low: ₹{fundamental_data.get('price_analysis', {}).get('52_week_low', 'N/A')}

        Please provide analysis in the following JSON format:
        {{
            "should_buy": true/false,
            "confidence_level": "High/Medium/Low",
            "target_price": number,
            "stop_loss": number,
            "time_horizon": "Short/Medium/Long term",
            "key_reasons": ["reason1", "reason2", "reason3"],
            "risks": ["risk1", "risk2"],
            "overall_score": number (1-100),
            "summary": "Brief summary of recommendation"
        }}

        Consider:
        1. Is the current price at a good entry point?
        2. Are technical indicators aligned for a buy signal?
        3. Are fundamentals strong enough to support the price?
        4. What should be the target price for 1:2 risk-reward ratio?
        5. Where should the stop-loss be placed?
        """

        return prompt

    def _parse_ai_response(self, ai_response, current_price):
        """Parse AI response and extract structured data"""
        try:
            # Try to extract JSON from the response
            start_idx = ai_response.find('{')
            end_idx = ai_response.rfind('}') + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = ai_response[start_idx:end_idx]
                analysis = json.loads(json_str)

                # Validate and set defaults
                analysis.setdefault('should_buy', False)
                analysis.setdefault('confidence_level', 'Low')
                analysis.setdefault('target_price', current_price * 1.1)
                analysis.setdefault('stop_loss', current_price * 0.95)
                analysis.setdefault('time_horizon', 'Medium term')
                analysis.setdefault('key_reasons', [])
                analysis.setdefault('risks', [])
                analysis.setdefault('overall_score', 50)
                analysis.setdefault('summary', 'Analysis completed')

                return analysis
            else:
                # If no JSON found, create analysis from text
                return self._extract_from_text(ai_response, current_price)

        except json.JSONDecodeError:
            # Fallback: try to extract information from text
            return self._extract_from_text(ai_response, current_price)
        except Exception as e:
            print(f"Error parsing AI response: {e}")
            return self._create_default_analysis(current_price)

    def _extract_from_text(self, text, current_price):
        """Extract analysis from plain text response"""
        text_lower = text.lower()

        # Simple keyword-based extraction
        should_buy = any(word in text_lower for word in ['buy', 'purchase', 'invest', 'positive'])
        should_not_buy = any(word in text_lower for word in ['sell', 'avoid', 'negative', 'risky'])

        if should_not_buy:
            should_buy = False

        confidence = 'Medium'
        if any(word in text_lower for word in ['strong', 'high confidence', 'definitely']):
            confidence = 'High'
        elif any(word in text_lower for word in ['weak', 'uncertain', 'maybe']):
            confidence = 'Low'

        return {
            'should_buy': should_buy,
            'confidence_level': confidence,
            'target_price': current_price * 1.1,
            'stop_loss': current_price * 0.95,
            'time_horizon': 'Medium term',
            'key_reasons': ['AI text analysis'],
            'risks': ['Market volatility'],
            'overall_score': 60 if should_buy else 40,
            'summary': text[:200] + '...' if len(text) > 200 else text,
            'ai_response_type': 'text_extraction'
        }

    def _create_default_analysis(self, current_price):
        """Create a default analysis when AI fails"""
        return {
            'should_buy': False,
            'confidence_level': 'Low',
            'target_price': current_price * 1.05,
            'stop_loss': current_price * 0.97,
            'time_horizon': 'Short term',
            'key_reasons': ['AI analysis unavailable'],
            'risks': ['Unable to perform comprehensive analysis'],
            'overall_score': 50,
            'summary': 'AI analysis failed, using default conservative approach',
            'ai_response_type': 'default'
        }

    def _fallback_analysis(self, current_price, technical_signals, fundamental_data):
        """Rule-based analysis when AI is not available"""
        try:
            buy_signals = 0
            total_signals = 0
            reasons = []
            risks = []

            # Technical analysis scoring
            signals = technical_signals.get('signals', {})

            for signal_name, signal_value in signals.items():
                total_signals += 1
                if signal_value == 'BUY':
                    buy_signals += 1
                    reasons.append(f"Technical: {signal_name.replace('_', ' ').title()} shows BUY")
                elif signal_value == 'SELL':
                    risks.append(f"Technical: {signal_name.replace('_', ' ').title()} shows SELL")

            # RSI specific check
            rsi = technical_signals.get('rsi', 50)
            if rsi and rsi < 30:
                buy_signals += 0.5
                reasons.append("RSI indicates oversold condition")
            elif rsi and rsi > 70:
                risks.append("RSI indicates overbought condition")

            # Fundamental analysis scoring
            fund_score = fundamental_data.get('fundamental_score', {}).get('score', 50)
            if fund_score >= 70:
                buy_signals += 1
                reasons.append("Strong fundamental score")
            elif fund_score <= 30:
                risks.append("Weak fundamental indicators")

            # P/E ratio check
            pe_ratio = fundamental_data.get('financial_ratios', {}).get('pe_ratio')
            if pe_ratio and 10 <= pe_ratio <= 25:
                buy_signals += 0.5
                reasons.append("Reasonable P/E ratio")
            elif pe_ratio and pe_ratio > 40:
                risks.append("High P/E ratio")

            # Price position relative to 52-week range
            price_analysis = fundamental_data.get('price_analysis', {})
            high_52w = price_analysis.get('52_week_high')
            low_52w = price_analysis.get('52_week_low')

            if high_52w and low_52w:
                position = (current_price - low_52w) / (high_52w - low_52w)
                if position < 0.3:  # In lower 30% of range
                    buy_signals += 0.5
                    reasons.append("Price near 52-week low")
                elif position > 0.8:  # In upper 20% of range
                    risks.append("Price near 52-week high")

            # Calculate recommendation (more lenient criteria)
            signal_strength = buy_signals / max(total_signals, 1) if total_signals > 0 else 0.5
            
            # More lenient BUY criteria for swing trading
            # Consider BUY if: 
            # - Good signal strength (>0.5) OR
            # - More buy signals than sell signals OR  
            # - Strong fundamentals with decent technicals
            has_positive_signals = buy_signals > 0
            has_strong_fundamentals = fund_score >= 60
            has_bullish_sentiment = technical_signals.get('overall_sentiment') == 'BULLISH'
            more_reasons_than_risks = len(reasons) >= len(risks)
            
            should_buy = (
                (signal_strength > 0.5 and more_reasons_than_risks) or
                (has_positive_signals and has_strong_fundamentals) or
                (has_bullish_sentiment and has_positive_signals and more_reasons_than_risks)
            )

            # Set confidence based on signal strength and data availability
            if signal_strength > 0.7 and has_strong_fundamentals and has_bullish_sentiment:
                confidence = "High"
            elif signal_strength > 0.5 and (has_strong_fundamentals or has_bullish_sentiment):
                confidence = "Medium"
            elif should_buy:
                confidence = "Medium"  # If we're recommending buy, at least medium confidence
            else:
                confidence = "Low"

            # Calculate targets
            support = technical_signals.get('support_resistance', {}).get('support', current_price * 0.95)
            resistance = technical_signals.get('support_resistance', {}).get('resistance', current_price * 1.1)

            target_price = min(resistance * 0.95, current_price * 1.15)  # Conservative target
            stop_loss = max(support * 1.05, current_price * 0.95)  # Conservative stop loss

            overall_score = min(100, max(0, int(signal_strength * 100)))

            return {
                'should_buy': should_buy,
                'confidence_level': confidence,
                'target_price': target_price,
                'stop_loss': stop_loss,
                'time_horizon': 'Medium term',
                'key_reasons': reasons[:3],  # Top 3 reasons
                'risks': risks[:3],  # Top 3 risks
                'overall_score': overall_score,
                'summary': f"Rule-based analysis: {'BUY' if should_buy else 'HOLD/AVOID'} with {confidence.lower()} confidence",
                'signal_strength': signal_strength,
                'ai_available': False,
                'analysis_type': 'rule_based'
            }

        except Exception as e:
            print(f"Error in fallback analysis: {e}")
            return self._create_default_analysis(current_price)

    def analyze_market_sentiment(self, market_data):
        """Analyze overall market sentiment"""
        if not self._available:
            return self._simple_market_analysis(market_data)

        try:
            prompt = f"""
            Analyze the following market data and provide sentiment analysis:

            Market Data: {market_data}

            Provide analysis in JSON format:
            {{
                "overall_sentiment": "Bullish/Bearish/Neutral",
                "confidence": "High/Medium/Low",
                "key_factors": ["factor1", "factor2"],
                "outlook": "Short term market outlook"
            }}
            """

            response = self.model.generate_content(prompt)
            return self._parse_market_response(response.text)

        except Exception as e:
            print(f"Market sentiment analysis error: {e}")
            return self._simple_market_analysis(market_data)

    def _simple_market_analysis(self, market_data):
        """Simple rule-based market analysis"""
        return {
            'overall_sentiment': 'Neutral',
            'confidence': 'Medium',
            'key_factors': ['Limited data available'],
            'outlook': 'Market analysis requires more comprehensive data',
            'ai_available': self._available
        }

    def _parse_market_response(self, response):
        """Parse market sentiment response"""
        try:
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                return self._simple_market_analysis({})

        except Exception as e:
            print(f"Error parsing market response: {e}")
            return self._simple_market_analysis({})