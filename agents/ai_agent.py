"""
AI Analysis Agent - MCP Agent for AI-powered recommendations
"""
from agents.base_agent import BaseAgent
from utils.ai_analyzer import AIAnalyzer
from typing import Dict, Any


class AIAnalysisAgent(BaseAgent):
    """Agent responsible for AI-powered analysis and recommendations"""
    
    def __init__(self):
        super().__init__("ai_analysis", "AI Analysis Agent")
        self.ai_analyzer = AIAnalyzer()
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process AI analysis request"""
        self.update_status("processing")
        
        try:
            symbol = context.get('symbol')
            current_price = context.get('current_price')
            technical_signals = context.get('technical_signals')
            fundamental_data = context.get('fundamental_data')
            
            if not all([symbol, current_price, technical_signals, fundamental_data]):
                return self.create_response(
                    False,
                    error="symbol, current_price, technical_signals, and fundamental_data required"
                )
            
            # Perform AI analysis
            analysis = self.ai_analyzer.analyze_buying_opportunity(
                symbol,
                float(current_price),
                technical_signals,
                fundamental_data
            )
            
            return self.create_response(True, data=analysis)
            
        except Exception as e:
            self.update_status("error")
            return self.create_response(False, error=str(e))
        finally:
            self.update_status("idle")
    
    def get_ai_status(self) -> Dict[str, Any]:
        """Get AI agent status"""
        return self.create_response(True, data={
            'ai_available': self.ai_analyzer.is_available(),
            'agent_status': self.get_status()
        })

