"""
Attorney-General.AI - Integration System

This module implements the integration system for the Attorney-General.AI backend.
It provides functionality for integrating with external services and APIs.
"""

import logging
from typing import Dict, Any, List, Optional
import aiohttp
import json
import os

logger = logging.getLogger(__name__)

class IntegrationSystem:
    """Integration system for connecting to external services."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the integration system.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.integrations = {}
        self.session = None
    
    async def initialize(self):
        """Initialize the integration system."""
        self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Close the integration system."""
        if self.session:
            await self.session.close()
            self.session = None
    
    def register_integration(self, name: str, integration_config: Dict[str, Any]) -> bool:
        """
        Register an integration.
        
        Args:
            name: The name of the integration
            integration_config: The integration configuration
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.integrations[name] = integration_config
            return True
        except Exception as e:
            logger.error(f"Error registering integration '{name}': {str(e)}")
            return False
    
    async def call_integration(
        self, 
        name: str, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Call an integration endpoint.
        
        Args:
            name: The name of the integration
            method: The HTTP method (GET, POST, PUT, DELETE)
            endpoint: The endpoint to call
            params: Optional query parameters
            data: Optional request body data
            headers: Optional request headers
            
        Returns:
            Dict[str, Any]: The response data
        """
        if name not in self.integrations:
            return {
                "error": f"Integration '{name}' not found"
            }
        
        if not self.session:
            await self.initialize()
        
        integration = self.integrations[name]
        base_url = integration.get("base_url", "")
        
        if not base_url:
            return {
                "error": f"Integration '{name}' has no base URL"
            }
        
        # Combine base URL and endpoint
        url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Combine headers
        all_headers = {}
        if "headers" in integration:
            all_headers.update(integration["headers"])
        if headers:
            all_headers.update(headers)
        
        try:
            # Make the request
            async with getattr(self.session, method.lower())(
                url,
                params=params,
                json=data,
                headers=all_headers
            ) as response:
                # Parse response
                if response.content_type == "application/json":
                    result = await response.json()
                else:
                    result = await response.text()
                
                return {
                    "status": response.status,
                    "data": result
                }
        except Exception as e:
            logger.error(f"Error calling integration '{name}': {str(e)}")
            return {
                "error": f"Error calling integration: {str(e)}"
            }
    
    async def get_available_integrations(self) -> List[str]:
        """
        Get a list of available integrations.
        
        Returns:
            List[str]: List of integration names
        """
        return list(self.integrations.keys())
    
    async def get_integration_config(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get the configuration for an integration.
        
        Args:
            name: The name of the integration
            
        Returns:
            Optional[Dict[str, Any]]: The integration configuration or None if not found
        """
        return self.integrations.get(name)
