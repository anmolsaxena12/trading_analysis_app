"""
Base Agent Class for MCP-based agents.
All agents inherit from this base class.

Status contract enforced here:
  - Call update_status("processing") at the START of process()
  - Call update_status("idle")  only on the SUCCESS path
  - Call update_status("error") only on the FAILURE path
  Never use a `finally` block that resets to "idle" — that silently
  overwrites error status and makes the /api/status endpoint useless.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import threading
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)


class BaseAgent(ABC):
    """Base class for all trading analysis agents."""

    def __init__(self, agent_id: str, agent_name: str):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.status = "initialized"
        self.last_execution: Optional[datetime] = None
        self.execution_count = 0
        self._lock = threading.Lock()

    @abstractmethod
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a request and return results.
        Must be implemented by each agent.

        Implementation MUST follow the status contract:
            self.update_status("processing")
            try:
                ...
                self.update_status("idle")
                return self.create_response(True, data=...)
            except Exception as e:
                self.update_status("error")
                return self.create_response(False, error=str(e))
        """
        pass

    def get_status(self) -> Dict[str, Any]:
        """Get agent status information."""
        with self._lock:
            return {
                'agent_id': self.agent_id,
                'agent_name': self.agent_name,
                'status': self.status,
                'last_execution': self.last_execution.isoformat() if self.last_execution else None,
                'execution_count': self.execution_count
            }

    def update_status(self, status: str):
        """Update agent status in a thread-safe way."""
        with self._lock:
            self.status = status
            self.last_execution = datetime.now()
            if status == "processing":
                self.execution_count += 1

    def validate_context(self, context: Dict[str, Any], required_keys: list) -> bool:
        """Validate that context contains all required keys."""
        return all(key in context for key in required_keys)

    def create_response(self, success: bool, data: Any = None, error: str = None) -> Dict[str, Any]:
        """Create a standardized response envelope."""
        response: Dict[str, Any] = {
            'agent_id': self.agent_id,
            'agent_name': self.agent_name,
            'success': success,
            'timestamp': datetime.now().isoformat()
        }
        if success:
            response['data'] = data
        else:
            response['error'] = error
            logger.warning("[%s] returning error response: %s", self.agent_id, error)
        return response
