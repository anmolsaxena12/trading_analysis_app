"""
MCP Server — Model Context Protocol server for agent communication.

Responsibilities:
  - Agent registry and request routing
  - Tool registry and tool dispatch (used by the AI agentic loop)
  - Bounded message history (deque, no memory leak)
"""
import json
import collections
from typing import Dict, Any, List, Optional
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)


class MCPServer:
    """MCP Server for agent communication and tool registration."""

    # Maximum number of messages kept in history (prevents unbounded memory growth)
    MAX_HISTORY = 500

    def __init__(self, server_name: str):
        self.server_name = server_name
        self.tools: Dict[str, Dict] = {}
        self.agents: Dict[str, Any] = {}
        # Bounded deque — oldest messages are automatically discarded
        self.message_history: collections.deque = collections.deque(maxlen=self.MAX_HISTORY)

    # ------------------------------------------------------------------
    # Tool registry
    # ------------------------------------------------------------------

    def register_tool(self, tool_name: str, tool_schema: Dict[str, Any], handler):
        """Register a callable tool with its JSON schema and handler function."""
        self.tools[tool_name] = {
            'schema': tool_schema,
            'handler': handler,
            'registered_at': datetime.now().isoformat()
        }
        logger.info("Registered tool: %s", tool_name)

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke a registered tool by name with the given arguments.
        Used by the AI agentic loop when Gemini issues a function call.
        """
        if tool_name not in self.tools:
            logger.warning("Tool not found: %s", tool_name)
            return {'success': False, 'error': f'Tool {tool_name} not found'}

        try:
            result = self.tools[tool_name]['handler'](**arguments)
            logger.info("Tool call succeeded: %s", tool_name)
            return {'success': True, 'result': result, 'tool': tool_name}
        except Exception as e:
            logger.error("Tool call failed: %s — %s", tool_name, e)
            return {'success': False, 'error': str(e), 'tool': tool_name}

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        Return tool schemas in a format suitable for passing to the Gemini
        function-calling API as `tools` parameter.
        Each entry is a dict with 'name', 'description', and 'parameters'.
        """
        return [
            {
                'name': name,
                'description': tool['schema'].get('description', ''),
                'parameters': tool['schema'].get('parameters', {})
            }
            for name, tool in self.tools.items()
        ]

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Return full tool metadata list (for status/debug endpoints)."""
        return [
            {
                'name': name,
                'schema': tool['schema'],
                'registered_at': tool['registered_at']
            }
            for name, tool in self.tools.items()
        ]

    # ------------------------------------------------------------------
    # Agent registry
    # ------------------------------------------------------------------

    def register_agent(self, agent_id: str, agent: Any):
        """Register an agent instance under the given ID."""
        self.agents[agent_id] = agent
        logger.info("Registered agent: %s (%s)", agent_id, agent.agent_name)

    def route_request(self, agent_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Route a request dict to the appropriate agent and record in history."""
        if agent_id not in self.agents:
            logger.error("Agent not found: %s", agent_id)
            return {'success': False, 'error': f'Agent {agent_id} not found'}

        agent = self.agents[agent_id]
        try:
            result = agent.process(context)
            self.message_history.append({
                'timestamp': datetime.now().isoformat(),
                'agent_id': agent_id,
                'context_keys': list(context.keys()),
                'success': result.get('success', False)
            })
            return result
        except Exception as e:
            logger.error("Routing error for agent %s: %s", agent_id, e)
            return {'success': False, 'error': str(e), 'agent_id': agent_id}

    def get_available_agents(self) -> List[Dict[str, Any]]:
        """Return status dicts for all registered agents."""
        return [agent.get_status() for agent in self.agents.values()]

    def get_history_summary(self) -> Dict[str, Any]:
        """Return a lightweight summary of recent message history."""
        return {
            'total_messages': len(self.message_history),
            'max_history': self.MAX_HISTORY,
            'recent': list(self.message_history)[-10:]
        }
