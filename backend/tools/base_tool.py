"""
Attorney-General.AI - Base Tool

This module defines the base tool class for the Attorney-General.AI backend.
It provides the foundation for specialized tools like legal research and document analysis.
"""

import logging
from typing import Dict, Any, List, Optional, Union
import uuid
import json
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class BaseTool:
    """Base tool class for Attorney-General.AI."""
    
    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the base tool.
        
        Args:
            name: Tool name
            description: Tool description
            parameters: Tool parameters schema
            config: Optional configuration
        """
        self.name = name
        self.description = description
        self.parameters = parameters
        self.config = config or {}
        
        # Initialize tool state
        self.usage_count = 0
        self.last_used = None
        self.metadata = {}
    
    async def run(self, **kwargs) -> Dict[str, Any]:
        """
        Run the tool with the provided parameters.
        
        Args:
            **kwargs: Tool parameters
            
        Returns:
            Dict[str, Any]: Tool result
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        Validate tool parameters.
        
        Args:
            parameters: Parameters to validate
            
        Returns:
            bool: True if parameters are valid
            
        Raises:
            ValueError: If parameters are invalid
        """
        # Basic validation - check if required parameters are present
        for param_name, param_spec in self.parameters.items():
            if param_spec.get("required", False) and param_name not in parameters:
                raise ValueError(f"Missing required parameter: {param_name}")
        
        return True
    
    def update_usage_stats(self) -> None:
        """Update tool usage statistics."""
        self.usage_count += 1
        self.last_used = datetime.utcnow()
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get tool usage statistics.
        
        Returns:
            Dict[str, Any]: Usage statistics
        """
        return {
            "name": self.name,
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat() if self.last_used else None
        }
    
    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set tool metadata.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
    
    def get_metadata(self, key: str) -> Optional[Any]:
        """
        Get tool metadata.
        
        Args:
            key: Metadata key
            
        Returns:
            Optional[Any]: Metadata value
        """
        return self.metadata.get(key)
