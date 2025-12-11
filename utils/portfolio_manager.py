from datetime import datetime, timedelta
import pandas as pd
import numpy as np

class PortfolioManager:
    def __init__(self, kite_handler):
        self.kite = kite_handler
        self.portfolio_cache = {}
        self.cache_expiry = timedelta(minutes=5)

    def is_connected(self):
        return self.kite and self.kite.is_connected()

    def get_holdings(self):
        """Get current holdings from Zerodha"""
        if not self.is_connected():
            return []

        try:
            # Check cache first
            cache_key = 'holdings'
            if cache_key in self.portfolio_cache:
                cache_time, data = self.portfolio_cache[cache_key]
                if datetime.now() - cache_time < self.cache_expiry:
                    return data

            holdings = self.kite.get_holdings()

            # Enhanced holdings with additional calculations
            enhanced_holdings = []
            for holding in holdings:
                if holding['quantity'] > 0:  # Only include actual holdings
                    current_value = holding['quantity'] * holding['last_price']
                    invested_value = holding['quantity'] * holding['average_price']
                    pnl = current_value - invested_value
                    pnl_percent = (pnl / invested_value) * 100 if invested_value > 0 else 0

                    enhanced_holding = {
                        'symbol': holding['tradingsymbol'],
                        'quantity': holding['quantity'],
                        'average_price': holding['average_price'],
                        'current_price': holding['last_price'],
                        'invested_value': invested_value,
                        'current_value': current_value,
                        'pnl': pnl,
                        'pnl_percent': pnl_percent,
                        'exchange': holding['exchange'],
                        'isin': holding.get('isin', ''),
                        'product': holding.get('product', 'CNC')
                    }
                    enhanced_holdings.append(enhanced_holding)

            # Cache the result
            self.portfolio_cache[cache_key] = (datetime.now(), enhanced_holdings)
            return enhanced_holdings

        except Exception as e:
            print(f"Error getting holdings: {e}")
            return []

    def get_positions(self):
        """Get current positions from Zerodha"""
        if not self.is_connected():
            return []

        try:
            cache_key = 'positions'
            if cache_key in self.portfolio_cache:
                cache_time, data = self.portfolio_cache[cache_key]
                if datetime.now() - cache_time < self.cache_expiry:
                    return data

            positions_data = self.kite.get_positions()
            all_positions = []

            # Process net positions
            for position in positions_data.get('net', []):
                if position['quantity'] != 0:  # Only include active positions
                    pnl_percent = (position['pnl'] / abs(position['quantity'] * position['average_price'])) * 100 if position['average_price'] > 0 else 0

                    enhanced_position = {
                        'symbol': position['tradingsymbol'],
                        'quantity': position['quantity'],
                        'average_price': position['average_price'],
                        'last_price': position['last_price'],
                        'pnl': position['pnl'],
                        'pnl_percent': pnl_percent,
                        'product': position['product'],
                        'exchange': position['exchange'],
                        'position_type': 'net'
                    }
                    all_positions.append(enhanced_position)

            # Cache the result
            self.portfolio_cache[cache_key] = (datetime.now(), all_positions)
            return all_positions

        except Exception as e:
            print(f"Error getting positions: {e}")
            return []

    def get_available_funds(self):
        """Get available funds for trading"""
        if not self.is_connected():
            return 0

        try:
            funds = self.kite.get_funds()
            equity_funds = funds.get('equity', {})
            available_cash = equity_funds.get('available', {}).get('cash', 0)
            return float(available_cash)

        except Exception as e:
            print(f"Error getting funds: {e}")
            return 0

    def get_portfolio_analysis(self):
        """Get comprehensive portfolio analysis"""
        try:
            holdings = self.get_holdings()
            positions = self.get_positions()
            available_funds = self.get_available_funds()

            # Combine holdings and positions
            all_instruments = holdings + positions

            if not all_instruments:
                return {
                    'total_invested': 0,
                    'current_value': 0,
                    'total_pnl': 0,
                    'total_pnl_percent': 0,
                    'available_funds': available_funds,
                    'instruments_count': 0,
                    'top_performers': [],
                    'worst_performers': [],
                    'sector_allocation': {},
                    'risk_analysis': 'No positions to analyze'
                }

            # Calculate totals
            total_invested = sum(abs(inst.get('invested_value', inst.get('quantity', 0) * inst.get('average_price', 0))) for inst in all_instruments)
            current_value = sum(abs(inst.get('current_value', inst.get('quantity', 0) * inst.get('last_price', inst.get('current_price', 0)))) for inst in all_instruments)
            total_pnl = sum(inst.get('pnl', 0) for inst in all_instruments)
            total_pnl_percent = (total_pnl / total_invested) * 100 if total_invested > 0 else 0

            # Find top and worst performers
            sorted_by_pnl = sorted([inst for inst in all_instruments if inst.get('pnl_percent') is not None], 
                                 key=lambda x: x.get('pnl_percent', 0), reverse=True)

            top_performers = sorted_by_pnl[:5]  # Top 5
            worst_performers = sorted_by_pnl[-5:] if len(sorted_by_pnl) > 5 else []

            # Risk analysis
            risk_analysis = self._analyze_portfolio_risk(all_instruments, total_invested)

            return {
                'total_invested': total_invested,
                'current_value': current_value,
                'total_pnl': total_pnl,
                'total_pnl_percent': total_pnl_percent,
                'available_funds': available_funds,
                'instruments_count': len(all_instruments),
                'holdings_count': len(holdings),
                'positions_count': len(positions),
                'top_performers': top_performers,
                'worst_performers': worst_performers,
                'risk_analysis': risk_analysis,
                'last_updated': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Error in portfolio analysis: {e}")
            return {'error': str(e)}

    def _analyze_portfolio_risk(self, instruments, total_invested):
        """Analyze portfolio risk"""
        try:
            if not instruments or total_invested == 0:
                return "No data for risk analysis"

            # Calculate concentration risk
            max_position_percent = 0
            positions_over_10_percent = 0
            losing_positions = 0

            for inst in instruments:
                position_value = abs(inst.get('current_value', inst.get('quantity', 0) * inst.get('last_price', inst.get('current_price', 0))))
                position_percent = (position_value / total_invested) * 100

                if position_percent > max_position_percent:
                    max_position_percent = position_percent

                if position_percent > 10:
                    positions_over_10_percent += 1

                if inst.get('pnl_percent', 0) < -5:  # Losing more than 5%
                    losing_positions += 1

            # Risk assessment
            risk_level = "Low"
            if max_position_percent > 30:
                risk_level = "High"
            elif max_position_percent > 20 or positions_over_10_percent > 3:
                risk_level = "Medium"

            if losing_positions > len(instruments) * 0.4:  # More than 40% losing positions
                risk_level = "High"

            return {
                'risk_level': risk_level,
                'max_position_percent': max_position_percent,
                'positions_over_10_percent': positions_over_10_percent,
                'losing_positions': losing_positions,
                'total_positions': len(instruments),
                'concentration_risk': 'High' if max_position_percent > 25 else 'Medium' if max_position_percent > 15 else 'Low',
                'diversification_score': min(100, max(0, 100 - max_position_percent))
            }

        except Exception as e:
            return f"Risk analysis error: {str(e)}"

    def get_sell_recommendations(self):
        """Get recommendations for which stocks to sell based on 1:2 risk-reward"""
        try:
            holdings = self.get_holdings()
            positions = self.get_positions()
            all_instruments = holdings + positions

            recommendations = []

            for instrument in all_instruments:
                symbol = instrument.get('symbol', '')
                current_price = instrument.get('current_price', instrument.get('last_price', 0))
                avg_price = instrument.get('average_price', 0)
                pnl_percent = instrument.get('pnl_percent', 0)
                quantity = instrument.get('quantity', 0)

                if quantity == 0 or avg_price == 0:
                    continue

                # Calculate risk-reward based targets
                target_profit_percent = 10  # Target 10% profit
                stop_loss_percent = 5   # Stop loss at 5%

                target_price = avg_price * (1 + target_profit_percent / 100)
                stop_loss_price = avg_price * (1 - stop_loss_percent / 100)

                # Determine recommendation
                action = None
                priority = "Low"
                reason = ""

                if current_price >= target_price:
                    action = "SELL"
                    priority = "High"
                    reason = f"Target profit of {target_profit_percent}% achieved. Book profits."
                elif current_price <= stop_loss_price:
                    action = "SELL"
                    priority = "Critical"
                    reason = f"Stop loss triggered. Limit losses."
                elif pnl_percent >= target_profit_percent * 0.8:  # 80% of target achieved
                    action = "PARTIAL_SELL"
                    priority = "Medium"
                    reason = f"Near target ({pnl_percent:.1f}%). Consider partial profit booking."
                elif pnl_percent <= -stop_loss_percent * 0.8:  # 80% of stop loss reached
                    action = "REVIEW"
                    priority = "Medium"
                    reason = f"Approaching stop loss. Review position carefully."

                if action:
                    recommendations.append({
                        'symbol': symbol,
                        'current_price': current_price,
                        'avg_price': avg_price,
                        'quantity': quantity,
                        'current_pnl_percent': pnl_percent,
                        'target_price': target_price,
                        'stop_loss_price': stop_loss_price,
                        'action': action,
                        'priority': priority,
                        'reason': reason,
                        'potential_pnl': quantity * (current_price - avg_price)
                    })

            # Sort by priority (Critical > High > Medium > Low)
            priority_order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}
            recommendations.sort(key=lambda x: priority_order.get(x['priority'], 4))

            return {
                'recommendations': recommendations,
                'total_positions_analyzed': len(all_instruments),
                'actions_recommended': len(recommendations),
                'critical_actions': len([r for r in recommendations if r['priority'] == 'Critical']),
                'high_priority_actions': len([r for r in recommendations if r['priority'] == 'High']),
                'analysis_timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Error generating sell recommendations: {e}")
            return {'error': str(e), 'recommendations': []}

    def get_position_summary(self):
        """Get a quick summary of positions"""
        try:
            holdings = self.get_holdings()
            positions = self.get_positions()

            profitable_count = 0
            losing_count = 0
            total_pnl = 0

            for instrument in holdings + positions:
                pnl = instrument.get('pnl', 0)
                total_pnl += pnl

                if pnl > 0:
                    profitable_count += 1
                elif pnl < 0:
                    losing_count += 1

            return {
                'total_positions': len(holdings) + len(positions),
                'holdings': len(holdings),
                'day_positions': len(positions),
                'profitable_positions': profitable_count,
                'losing_positions': losing_count,
                'total_pnl': total_pnl,
                'win_rate': (profitable_count / (profitable_count + losing_count)) * 100 if (profitable_count + losing_count) > 0 else 0
            }

        except Exception as e:
            print(f"Error in position summary: {e}")
            return {'error': str(e)}

    def clear_cache(self):
        """Clear portfolio cache"""
        self.portfolio_cache.clear()