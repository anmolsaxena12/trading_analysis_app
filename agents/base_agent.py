"""
Base Agent Class for MCP-based agents
All agents inherit from this base class
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import json
from datetime import datetime


class BaseAgent(ABC):
    """Base class for all trading analysis agents"""
    
    def __init__(self, agent_id: str, agent_name: str):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.status = "initialized"
        self.last_execution = None
        self.execution_count = 0
        
    @abstractmethod
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a request and return results
        Must be implemented by each agent
        """
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status information"""
        return {
            'agent_id': self.agent_id,
            'agent_name': self.agent_name,
            'status': self.status,
            'last_execution': self.last_execution.isoformat() if self.last_execution else None,
            'execution_count': self.execution_count
        }
    
    def update_status(self, status: str):
        """Update agent status"""
        self.status = status
        self.last_execution = datetime.now()
        self.execution_count += 1
    
    def validate_context(self, context: Dict[str, Any], required_keys: list) -> bool:
        """Validate that context contains required keys"""
        return all(key in context for key in required_keys)
    
    def create_response(self, success: bool, data: Any = None, error: str = None) -> Dict[str, Any]:
        """Create standardized response"""
        response = {
            'agent_id': self.agent_id,
            'agent_name': self.agent_name,
            'success': success,
            'timestamp': datetime.now().isoformat()
        }
        
        if success:
            response['data'] = data
        else:
            response['error'] = error
            
        return response

