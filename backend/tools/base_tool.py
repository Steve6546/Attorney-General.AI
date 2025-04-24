"""
Attorney-General.AI - Base Tool

This module defines the base tool class that all specialized tools inherit from.
It provides common functionality and interfaces for all tools.
"""

from typing import Dict, Any, Optional
import logging
import json

logger = logging.getLogger(__name__)

class BaseTool:
    """Base class for all tools in the system."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base tool.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.name = "base_tool"
        self.description = "Base tool class that should be extended."
        self.parameters = {}
        self.required_parameters = []
    
    async def execute(self, params: Dict[str, Any]) -> Any:
        """
        Execute the tool with the given parameters.
        
        Args:
            params: The parameters to pass to the tool
            
        Returns:
            Any: The tool execution result
        """
        # This method should be overridden by subclasses
        raise NotImplementedError("Method not implemented in base class")
    
    def get_description(self) -> Dict[str, Any]:
        """
        Get the tool description for LLM function calling.
        
        Returns:
            Dict[str, Any]: The tool description
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                    "required": self.required_parameters
                }
            }
        }
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """
        Validate that all required parameters are present.
        
        Args:
            params: The parameters to validate
            
        Returns:
            bool: True if all required parameters are present, False otherwise
        """
        for param in self.required_parameters:
            if param not in params:
                return False
        return True
