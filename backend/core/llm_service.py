"""
Attorney-General.AI - LLM Service

This module provides a service for interacting with Large Language Models (LLMs).
It abstracts the communication with different LLM providers.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
import openai

from backend.config.settings import settings

logger = logging.getLogger(__name__)

class LLMService:
    """Service for interacting with Large Language Models."""
    
    def __init__(self):
        """Initialize the LLM service."""
        self.api_key = settings.OPENAI_API_KEY
        self.default_model = settings.DEFAULT_LLM_MODEL
        
        # Set OpenAI API key
        openai.api_key = self.api_key
    
    async def generate_response(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system_message: Optional[str] = None
    ) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The user prompt
            model: The LLM model to use (defaults to the configured default)
            temperature: The sampling temperature
            max_tokens: The maximum number of tokens to generate
            system_message: Optional system message to set context
            
        Returns:
            str: The generated response
        """
        try:
            # Use the specified model or default
            model_name = model or self.default_model
            
            # Prepare messages
            messages = []
            
            # Add system message if provided
            if system_message:
                messages.append({"role": "system", "content": system_message})
            
            # Add user message
            messages.append({"role": "user", "content": prompt})
            
            # Call the OpenAI API
            response = await openai.ChatCompletion.acreate(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Extract and return the response text
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            return f"I apologize, but I encountered an error: {str(e)}"
    
    async def generate_with_tools(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a response from the LLM with tool calling capabilities.
        
        Args:
            prompt: The user prompt
            tools: List of tool definitions
            model: The LLM model to use (defaults to the configured default)
            temperature: The sampling temperature
            max_tokens: The maximum number of tokens to generate
            system_message: Optional system message to set context
            
        Returns:
            Dict[str, Any]: The generated response with tool calls if any
        """
        try:
            # Use the specified model or default
            model_name = model or self.default_model
            
            # Prepare messages
            messages = []
            
            # Add system message if provided
            if system_message:
                messages.append({"role": "system", "content": system_message})
            
            # Add user message
            messages.append({"role": "user", "content": prompt})
            
            # Call the OpenAI API with tools
            response = await openai.ChatCompletion.acreate(
                model=model_name,
                messages=messages,
                tools=tools,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Process the response
            message = response.choices[0].message
            
            # Check if there are tool calls
            if hasattr(message, 'tool_calls') and message.tool_calls:
                return {
                    "content": message.content,
                    "tool_calls": message.tool_calls,
                    "has_tool_calls": True
                }
            else:
                return {
                    "content": message.content,
                    "has_tool_calls": False
                }
                
        except Exception as e:
            logger.error(f"Error generating LLM response with tools: {str(e)}")
            return {
                "content": f"I apologize, but I encountered an error: {str(e)}",
                "has_tool_calls": False
            }
