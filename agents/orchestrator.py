"""
Agent Orchestrator - Coordinates multiple agents using MCP
"""
from agents.mcp_server import MCPServer
from agents.stock_search_agent import StockSearchAgent
from agents.technical_agent import TechnicalAnalysisAgent
from agents.fundamental_agent import FundamentalAnalysisAgent
from agents.risk_agent import RiskManagementAgent
from agents.ai_agent import AIAnalysisAgent
from agents.portfolio_agent import PortfolioAgent
from utils.kite_handler import KiteHandler
from typing import Dict, Any, List
import traceback


class AgentOrchestrator:
    """Orchestrates multiple agents for trading analysis"""
    
    def __init__(self, kite_handler: KiteHandler = None):
        self.mcp_server = MCPServer("trading_analysis_mcp")
        
        # Initialize all agents
        self.stock_search_agent = StockSearchAgent()
        self.technical_agent = TechnicalAnalysisAgent()
        self.fundamental_agent = FundamentalAnalysisAgent()
        self.risk_agent = RiskManagementAgent()
        self.ai_agent = AIAnalysisAgent()
        self.portfolio_agent = PortfolioAgent(kite_handler)
        
        # Register agents with MCP server
        self.mcp_server.register_agent("stock_search", self.stock_search_agent)
        self.mcp_server.register_agent("technical_analysis", self.technical_agent)
        self.mcp_server.register_agent("fundamental_analysis", self.fundamental_agent)
        self.mcp_server.register_agent("risk_management", self.risk_agent)
        self.mcp_server.register_agent("ai_analysis", self.ai_agent)
        self.mcp_server.register_agent("portfolio", self.portfolio_agent)
        
        print("✓ Agent Orchestrator initialized with MCP server")
        print(f"  Registered {len(self.mcp_server.agents)} agents")
    
    def analyze_stock(self, symbol: str) -> Dict[str, Any]:
        """Orchestrate full stock analysis using multiple agents"""
        try:
            # Step 1: Validate and get stock data (Stock Search Agent)
            search_result = self.mcp_server.route_request("stock_search", {
                'action': 'search',
                'symbol': symbol
            })
            
            if not search_result.get('success'):
                return {'error': search_result.get('error', 'Stock search failed')}
            
            symbol_data = search_result['data']
            current_price = symbol_data['current_price']
            
            # Step 2: Get stock data for analysis (Fundamental Agent)
            stock_data_result = self.mcp_server.route_request("fundamental_analysis", {
                'action': 'get_stock_data',
                'symbol': symbol
            })
            
            if not stock_data_result.get('success'):
                return {'error': 'Could not fetch stock data'}
            
            # Step 3: Technical Analysis (Technical Agent)
            from utils.fundamental_analyzer import FundamentalAnalyzer
            fa = FundamentalAnalyzer()
            stock_data = fa.get_stock_data(symbol)
            
            technical_result = self.mcp_server.route_request("technical_analysis", {
                'symbol': symbol,
                'stock_data': stock_data
            })
            
            if not technical_result.get('success'):
                return {'error': technical_result.get('error', 'Technical analysis failed')}
            
            technical_signals = technical_result['data']
            
            # Step 4: Fundamental Analysis (Fundamental Agent)
            fundamental_result = self.mcp_server.route_request("fundamental_analysis", {
                'symbol': symbol
            })
            
            if not fundamental_result.get('success'):
                return {'error': fundamental_result.get('error', 'Fundamental analysis failed')}
            
            fundamental_data = fundamental_result['data']
            
            # Step 5: AI Analysis (AI Agent)
            ai_result = self.mcp_server.route_request("ai_analysis", {
                'symbol': symbol,
                'current_price': current_price,
                'technical_signals': technical_signals,
                'fundamental_data': fundamental_data
            })
            
            if not ai_result.get('success'):
                return {'error': ai_result.get('error', 'AI analysis failed')}
            
            buying_analysis = ai_result['data']
            
            # Step 6: Risk-Reward Analysis (Risk Agent)
            risk_reward = None
            if buying_analysis.get('should_buy', False):
                risk_result = self.mcp_server.route_request("risk_management", {
                    'action': 'calculate_risk_reward',
                    'entry_price': current_price,
                    'target_price': buying_analysis.get('target_price', current_price * 1.1),
                    'stop_loss': buying_analysis.get('stop_loss', current_price * 0.95)
                })
                
                if risk_result.get('success'):
                    risk_reward = risk_result['data']
            
            # Compile results
            return {
                'symbol': symbol,
                'current_price': current_price,
                'technical_analysis': technical_signals,
                'fundamental_analysis': fundamental_data,
                'buying_analysis': buying_analysis,
                'risk_reward': risk_reward,
                'agents_used': [
                    'stock_search',
                    'technical_analysis',
                    'fundamental_analysis',
                    'ai_analysis',
                    'risk_management'
                ]
            }
            
        except Exception as e:
            print(f"Orchestration error: {traceback.format_exc()}")
            return {'error': str(e)}
    
    def scan_stocks(self, symbols: List[str] = None, min_score: int = 60, max_results: int = 20) -> Dict[str, Any]:
        """Orchestrate stock scanning using multiple agents"""
        try:
            # Use Stock Search Agent to get available stocks
            if symbols is None:
                symbols = self.stock_search_agent.default_stocks
            
            scan_result = self.mcp_server.route_request("stock_search", {
                'action': 'scan',
                'symbols': symbols,
                'max_results': max_results
            })
            
            if not scan_result.get('success'):
                return {'error': scan_result.get('error', 'Stock scan failed')}
            
            available_stocks = scan_result['data']['stocks']
            recommendations = []
            
            # Analyze each stock using full analysis pipeline
            for stock_info in available_stocks[:max_results]:
                symbol = stock_info['symbol']
                analysis = self.analyze_stock(symbol)
                
                if 'error' not in analysis:
                    # Calculate overall score
                    overall_score = self._calculate_overall_score(analysis)
                    
                    if overall_score >= min_score:
                        # Format recommendation similar to old stock_scanner format
                        buying_analysis = analysis.get('buying_analysis', {})
                        risk_reward = analysis.get('risk_reward', {})
                        current_price = analysis.get('current_price', 0)
                        target_price = buying_analysis.get('target_price', current_price * 1.1)
                        stop_loss = buying_analysis.get('stop_loss', current_price * 0.95)
                        
                        # Create timeline
                        from datetime import datetime, timedelta
                        buy_date = datetime.now()
                        sell_date = buy_date + timedelta(days=21)  # Default 3 weeks
                        timeline = {
                            'buy_date': buy_date.strftime('%Y-%m-%d'),
                            'expected_sell_date': sell_date.strftime('%Y-%m-%d'),
                            'days_holding': 21,
                            'time_horizon': buying_analysis.get('time_horizon', 'Medium term')
                        }
                        
                        recommendation = {
                            'symbol': symbol,
                            'company_name': analysis.get('fundamental_analysis', {}).get('company_name', symbol),
                            'current_price': float(current_price),
                            'buy_price': float(current_price),
                            'target_price': float(target_price),
                            'stop_loss': float(stop_loss),
                            'risk_reward': risk_reward if risk_reward else {
                                'entry_price': float(current_price),
                                'target_price': float(target_price),
                                'stop_loss_price': float(stop_loss),
                                'risk_reward_ratio': 2.0,
                                'ratio_formatted': '1:2.00',
                                'is_favorable': True
                            },
                            'overall_score': float(overall_score),
                            'technical_score': 50.0,  # Simplified
                            'fundamental_score': float(analysis.get('fundamental_analysis', {}).get('fundamental_score', {}).get('score', 50)),
                            'ai_score': float(buying_analysis.get('overall_score', 50)),
                            'confidence': buying_analysis.get('confidence_level', 'Medium'),
                            'timeline': timeline,
                            'key_reasons': buying_analysis.get('key_reasons', [])[:3],
                            'risks': buying_analysis.get('risks', [])[:2],
                            'sector': analysis.get('fundamental_analysis', {}).get('sector_info', {}).get('sector', 'Unknown'),
                            'technical_signals': {
                                'rsi': analysis.get('technical_analysis', {}).get('rsi'),
                                'macd_signal': analysis.get('technical_analysis', {}).get('signals', {}).get('macd_signal'),
                                'trend_signal': analysis.get('technical_analysis', {}).get('signals', {}).get('trend_signal'),
                                'overall_sentiment': analysis.get('technical_analysis', {}).get('overall_sentiment')
                            },
                            'potential_profit_percent': float(((target_price - current_price) / current_price) * 100),
                            'risk_percent': float(((current_price - stop_loss) / current_price) * 100),
                            'scanned_at': datetime.now().isoformat()
                        }
                        
                        recommendations.append(recommendation)
            
            # Sort by score
            recommendations.sort(key=lambda x: x['overall_score'], reverse=True)
            
            return {
                'recommendations': recommendations[:max_results],
                'count': len(recommendations),
                'agents_used': ['stock_search', 'technical_analysis', 'fundamental_analysis', 'ai_analysis', 'risk_management']
            }
            
        except Exception as e:
            print(f"Scan orchestration error: {traceback.format_exc()}")
            return {'error': str(e)}
    
    def _calculate_overall_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate overall recommendation score"""
        try:
            technical = analysis.get('technical_analysis', {})
            fundamental = analysis.get('fundamental_analysis', {})
            buying = analysis.get('buying_analysis', {})
            
            tech_score = 50  # Default
            if technical.get('overall_sentiment') == 'BULLISH':
                tech_score = 70
            elif technical.get('overall_sentiment') == 'BEARISH':
                tech_score = 30
            
            fund_score = fundamental.get('fundamental_score', {}).get('score', 50)
            ai_score = buying.get('overall_score', 50)
            
            # Weighted average
            overall = (tech_score * 0.4) + (fund_score * 0.3) + (ai_score * 0.3)
            return float(overall)
        except:
            return 50.0
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        return {
            'mcp_server': self.mcp_server.server_name,
            'agents': self.mcp_server.get_available_agents(),
            'total_agents': len(self.mcp_server.agents)
        }

