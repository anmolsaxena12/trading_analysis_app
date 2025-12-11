import numpy as np
from datetime import datetime
import pandas as pd

class RiskManager:
    def __init__(self, default_risk_per_trade=0.02):
        self.default_risk_per_trade = default_risk_per_trade  # 2% of portfolio per trade
        self.target_risk_reward_ratio = 2.0  # 1:2 minimum

    def calculate_risk_reward(self, entry_price, target_price, stop_loss_price):
        """Calculate risk-reward ratio"""
        try:
            risk = abs(entry_price - stop_loss_price)
            reward = abs(target_price - entry_price)

            if risk == 0:
                return None

            ratio = reward / risk

            # Calculate breakeven win rate
            breakeven_rate = 1 / (1 + ratio)

            return {
                'entry_price': float(entry_price),
                'target_price': float(target_price),
                'stop_loss_price': float(stop_loss_price),
                'risk_amount': float(risk),
                'reward_amount': float(reward),
                'risk_reward_ratio': float(ratio),
                'ratio_formatted': f"1:{ratio:.2f}",
                'breakeven_win_rate': float(breakeven_rate * 100),
                'is_favorable': bool(ratio >= self.target_risk_reward_ratio),
                'recommendation': self._get_ratio_recommendation(ratio)
            }

        except Exception as e:
            print(f"Error calculating risk-reward: {e}")
            return None

    def _get_ratio_recommendation(self, ratio):
        """Get recommendation based on risk-reward ratio"""
        if ratio >= 3.0:
            return "Excellent - Very favorable risk-reward"
        elif ratio >= 2.0:
            return "Good - Meets minimum 1:2 requirement"
        elif ratio >= 1.5:
            return "Moderate - Below ideal but acceptable"
        elif ratio >= 1.0:
            return "Poor - Equal risk-reward, reconsider"
        else:
            return "Very Poor - Risk exceeds reward, avoid"

    def calculate_position_size(self, available_capital, entry_price, risk_reward_data, 
                               risk_per_trade=None):
        """Calculate position size based on risk management"""
        try:
            if not risk_reward_data or available_capital <= 0:
                return None

            risk_percent = risk_per_trade or self.default_risk_per_trade
            max_risk_amount = available_capital * risk_percent

            risk_per_share = risk_reward_data['risk_amount']

            if risk_per_share <= 0:
                return None

            # Calculate maximum shares based on risk
            max_shares = int(max_risk_amount / risk_per_share)

            # Calculate maximum shares based on available capital
            max_shares_by_capital = int(available_capital / entry_price)

            # Use the smaller of the two
            recommended_shares = min(max_shares, max_shares_by_capital)

            if recommended_shares <= 0:
                return None

            # Calculate actual investment and risk
            total_investment = recommended_shares * entry_price
            total_risk = recommended_shares * risk_per_share
            potential_profit = recommended_shares * risk_reward_data['reward_amount']

            return {
                'recommended_shares': recommended_shares,
                'total_investment': total_investment,
                'total_risk_amount': total_risk,
                'potential_profit': potential_profit,
                'risk_percentage': (total_risk / available_capital) * 100,
                'capital_utilization': (total_investment / available_capital) * 100,
                'max_loss_per_share': risk_per_share,
                'target_profit_per_share': risk_reward_data['reward_amount'],
                'position_size_rationale': f"Risk {risk_percent*100:.1f}% of capital per trade"
            }

        except Exception as e:
            print(f"Error calculating position size: {e}")
            return None

    def analyze_portfolio_risk(self, positions, current_prices):
        """Analyze overall portfolio risk"""
        try:
            total_value = 0
            total_risk = 0
            positions_at_risk = 0

            portfolio_analysis = []

            for position in positions:
                symbol = position.get('tradingsymbol', '')
                quantity = position.get('quantity', 0)
                avg_price = position.get('average_price', 0)
                current_price = current_prices.get(symbol, avg_price)

                if quantity == 0:
                    continue

                position_value = quantity * current_price
                position_pnl = (current_price - avg_price) * quantity
                position_pnl_percent = (position_pnl / (quantity * avg_price)) * 100 if avg_price > 0 else 0

                total_value += abs(position_value)

                # Consider position at risk if loss > 5%
                if position_pnl_percent < -5:
                    positions_at_risk += 1
                    total_risk += abs(position_pnl)

                portfolio_analysis.append({
                    'symbol': symbol,
                    'quantity': quantity,
                    'avg_price': avg_price,
                    'current_price': current_price,
                    'position_value': position_value,
                    'pnl': position_pnl,
                    'pnl_percent': position_pnl_percent,
                    'risk_level': self._assess_position_risk(position_pnl_percent)
                })

            return {
                'total_portfolio_value': total_value,
                'positions_analyzed': len(positions),
                'positions_at_risk': positions_at_risk,
                'total_unrealized_risk': total_risk,
                'risk_percentage': (total_risk / total_value) * 100 if total_value > 0 else 0,
                'position_details': portfolio_analysis,
                'risk_assessment': self._assess_portfolio_risk(positions_at_risk, len(positions))
            }

        except Exception as e:
            print(f"Error analyzing portfolio risk: {e}")
            return None

    def _assess_position_risk(self, pnl_percent):
        """Assess individual position risk level"""
        if pnl_percent >= 10:
            return "Low Risk - Strong Profit"
        elif pnl_percent >= 0:
            return "Low Risk - Profitable"
        elif pnl_percent >= -5:
            return "Moderate Risk - Minor Loss"
        elif pnl_percent >= -15:
            return "High Risk - Significant Loss"
        else:
            return "Very High Risk - Major Loss"

    def _assess_portfolio_risk(self, positions_at_risk, total_positions):
        """Assess overall portfolio risk"""
        if total_positions == 0:
            return "No positions"

        risk_ratio = positions_at_risk / total_positions

        if risk_ratio <= 0.1:
            return "Low Risk - Well managed portfolio"
        elif risk_ratio <= 0.3:
            return "Moderate Risk - Some positions need attention"
        elif risk_ratio <= 0.5:
            return "High Risk - Multiple positions at risk"
        else:
            return "Very High Risk - Portfolio needs immediate attention"

    def generate_sell_recommendations(self, positions, current_prices, target_ratio=2.0):
        """Generate sell recommendations to maintain 1:2 risk-reward ratio"""
        recommendations = []

        try:
            for position in positions:
                symbol = position.get('tradingsymbol', '')
                quantity = position.get('quantity', 0)
                avg_price = position.get('average_price', 0)
                current_price = current_prices.get(symbol, avg_price)

                if quantity <= 0 or avg_price <= 0:
                    continue

                # Calculate current P&L
                pnl_per_share = current_price - avg_price
                pnl_percent = (pnl_per_share / avg_price) * 100

                # Determine action based on risk-reward
                recommendation = self._get_sell_recommendation(
                    symbol, current_price, avg_price, pnl_percent, target_ratio
                )

                if recommendation:
                    recommendations.append(recommendation)

            return {
                'recommendations': recommendations,
                'total_positions_analyzed': len(positions),
                'positions_with_actions': len(recommendations),
                'analysis_timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Error generating sell recommendations: {e}")
            return {'recommendations': [], 'error': str(e)}

    def _get_sell_recommendation(self, symbol, current_price, avg_price, pnl_percent, target_ratio):
        """Get specific sell recommendation for a position"""
        try:
            # Calculate target profit (for 1:2 ratio, need 2x the acceptable loss)
            acceptable_loss_percent = 5  # 5% stop loss
            target_profit_percent = acceptable_loss_percent * target_ratio  # 10% for 1:2

            target_sell_price = avg_price * (1 + target_profit_percent / 100)
            stop_loss_price = avg_price * (1 - acceptable_loss_percent / 100)

            action = None
            priority = "Low"
            reason = ""

            if current_price >= target_sell_price:
                action = "SELL"
                priority = "High"
                reason = f"Target profit of {target_profit_percent:.1f}% achieved"
            elif current_price <= stop_loss_price:
                action = "SELL"
                priority = "Critical"
                reason = f"Stop loss triggered at -{acceptable_loss_percent:.1f}%"
            elif pnl_percent >= target_profit_percent * 0.8:  # 80% of target
                action = "CONSIDER_PARTIAL_SELL"
                priority = "Medium"
                reason = f"Near target profit ({pnl_percent:.1f}%), consider partial booking"
            elif pnl_percent <= -acceptable_loss_percent * 0.8:  # 80% of stop loss
                action = "MONITOR_CLOSELY"
                priority = "Medium"
                reason = f"Approaching stop loss level ({pnl_percent:.1f}%)"

            if action:
                return {
                    'symbol': symbol,
                    'current_price': current_price,
                    'avg_price': avg_price,
                    'current_pnl_percent': pnl_percent,
                    'target_sell_price': target_sell_price,
                    'stop_loss_price': stop_loss_price,
                    'action': action,
                    'priority': priority,
                    'reason': reason,
                    'risk_reward_ratio': f"1:{target_ratio}"
                }

            return None

        except Exception as e:
            print(f"Error getting sell recommendation for {symbol}: {e}")
            return None