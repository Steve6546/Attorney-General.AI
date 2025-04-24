"""
Attorney-General.AI - Base Agent

This module defines the base agent class that all specialized agents inherit from.
It provides common functionality and interfaces for all agents.
"""

from typing import Dict, Any, List, Optional
import logging
import uuid
import asyncio

from backend.core.llm_service import LLMService
from backend.utils.prompt_loader import load_prompt

logger = logging.getLogger(__name__)

class BaseAgent:
    """Base class for all agents in the system."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base agent.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.agent_type = "base_agent"
        self.capabilities = []
        self.llm_service = LLMService()
        self.tools = {}
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a request and return a response.
        
        Args:
            request: The request dictionary
            
        Returns:
            Dict[str, Any]: The response dictionary
        """
        # This method should be overridden by subclasses
        return {
            "status": "error",
            "data": "Method not implemented in base class"
        }
    
    async def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool with the given parameters.
        
        Args:
            tool_name: The name of the tool to execute
            params: The parameters to pass to the tool
            
        Returns:
            Dict[str, Any]: The tool execution result
        """
        if tool_name not in self.tools:
            return {
                "status": "error",
                "data": f"Tool '{tool_name}' not found"
            }
        
        try:
            tool = self.tools[tool_name]
            result = await tool.execute(params)
            return {
                "status": "success",
                "data": result
            }
        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {str(e)}")
            return {
                "status": "error",
                "data": f"Error executing tool: {str(e)}"
            }
    
    def register_tool(self, tool_name: str, tool_instance: Any) -> None:
        """
        Register a tool with the agent.
        
        Args:
            tool_name: The name of the tool
            tool_instance: The tool instance
        """
        self.tools[tool_name] = tool_instance
    
    def get_tool_descriptions(self) -> List[Dict[str, Any]]:
        """
        Get descriptions of all registered tools for LLM function calling.
        
        Returns:
            List[Dict[str, Any]]: List of tool descriptions
        """
        tool_descriptions = []
        
        for tool_name, tool in self.tools.items():
            if hasattr(tool, 'get_description'):
                tool_descriptions.append(tool.get_description())
        
        return tool_descriptions
    
    async def generate_response(
        self, 
        prompt: str, 
        system_message: Optional[str] = None
    ) -> str:
        """
        Generate a response using the LLM service.
        
        Args:
            prompt: The prompt to send to the LLM
            system_message: Optional system message
            
        Returns:
            str: The generated response
        """
        return await self.llm_service.generate_response(
            prompt=prompt,
            system_message=system_message
        )
    
    async def generate_with_tools(
        self,
        prompt: str,
        system_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a response with tool calling capabilities.
        
        Args:
            prompt: The prompt to send to the LLM
            system_message: Optional system message
            
        Returns:
            Dict[str, Any]: The generated response with tool calls if any
        """
        tool_descriptions = self.get_tool_descriptions()
        
        return await self.llm_service.generate_with_tools(
            prompt=prompt,
            tools=tool_descriptions,
            system_message=system_message
        )
    
    async def handle_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Handle tool calls from the LLM.
        
        Args:
            tool_calls: List of tool calls from the LLM
            
        Returns:
            List[Dict[str, Any]]: Results of the tool executions
        """
        results = []
        
        for tool_call in tool_calls:
            tool_name = tool_call.get('name')
            arguments = tool_call.get('arguments', {})
            
            if isinstance(arguments, str):
                try:
                    # Parse JSON string arguments
                    arguments = json.loads(arguments)
                except:
                    arguments = {"text": arguments}
            
            result = await self.execute_tool(tool_name, arguments)
            results.append({
                "tool_call_id": tool_call.get('id'),
                "tool_name": tool_name,
                "result": result
            })
        
        return results
