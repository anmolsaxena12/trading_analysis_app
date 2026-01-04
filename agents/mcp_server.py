"""
MCP Server Implementation
Model Context Protocol server for agent communication
"""
import json
from typing import Dict, Any, List, Optional
from datetime import datetime


class MCPServer:
    """MCP Server for agent communication and tool registration"""
    
    def __init__(self, server_name: str):
        self.server_name = server_name
        self.tools: Dict[str, Dict] = {}
        self.agents: Dict[str, Any] = {}
        self.message_history: List[Dict] = []
        
    def register_tool(self, tool_name: str, tool_schema: Dict[str, Any], handler):
        """Register a tool with the MCP server"""
        self.tools[tool_name] = {
            'schema': tool_schema,
            'handler': handler,
            'registered_at': datetime.now().isoformat()
        }
    
    def register_agent(self, agent_id: str, agent: Any):
        """Register an agent with the MCP server"""
        self.agents[agent_id] = agent
        print(f"✓ Registered agent: {agent_id} ({agent.agent_name})")
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a registered tool"""
        if tool_name not in self.tools:
            return {
                'success': False,
                'error': f'Tool {tool_name} not found'
            }
        
        try:
            tool = self.tools[tool_name]
            result = tool['handler'](**arguments)
            return {
                'success': True,
                'result': result,
                'tool': tool_name
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'tool': tool_name
            }
    
    def route_request(self, agent_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Route a request to the appropriate agent"""
        if agent_id not in self.agents:
            return {
                'success': False,
                'error': f'Agent {agent_id} not found'
            }
        
        agent = self.agents[agent_id]
        try:
            result = agent.process(context)
            self.message_history.append({
                'timestamp': datetime.now().isoformat(),
                'agent_id': agent_id,
                'context': context,
                'result': result
            })
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'agent_id': agent_id
            }
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools"""
        return [
            {
                'name': name,
                'schema': tool['schema'],
                'registered_at': tool['registered_at']
            }
            for name, tool in self.tools.items()
        ]
    
    def get_available_agents(self) -> List[Dict[str, Any]]:
        """Get list of available agents"""
        return [
            agent.get_status()
            for agent in self.agents.values()
        ]

