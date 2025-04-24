"""
LLM Service for Attorney-General.AI.

This module provides integration with language models for text generation and embeddings.
"""

import logging
import os
import json
import asyncio
from typing import List, Dict, Any, Optional, Union
import openai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from backend.config.settings import settings

# Configure logging
logger = logging.getLogger(__name__)

class LLMService:
    """Service for interacting with language models."""
    
    def __init__(self):
        """Initialize the LLM service."""
        # Configure OpenAI API
        openai.api_key = settings.OPENAI_API_KEY
        
        # Set default parameters
        self.default_params = {
            "temperature": 0.7,
            "max_tokens": 1000,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        }
        
        logger.info(f"LLM Service initialized with model: {settings.LLM_MODEL}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((openai.error.APIError, openai.error.Timeout, openai.error.ServiceUnavailableError))
    )
    def generate_response(
        self, 
        prompt: str, 
        max_tokens: int = None, 
        temperature: float = None,
        system: str = None,
        user: str = None,
        assistant: str = None,
        history: List[Dict[str, str]] = None
    ) -> str:
        """
        Generate a response from the language model.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            system: System message
            user: User message
            assistant: Assistant message
            history: Conversation history
            
        Returns:
            str: Generated response
        """
        try:
            # Format prompt if components are provided
            if system or user or assistant or history:
                prompt = self._format_prompt(system, user, assistant, history)
            
            # Set parameters
            params = self.default_params.copy()
            if max_tokens:
                params["max_tokens"] = max_tokens
            if temperature is not None:
                params["temperature"] = temperature
            
            # Generate response
            response = openai.Completion.create(
                model=settings.LLM_MODEL,
                prompt=prompt,
                **params
            )
            
            # Extract and return text
            return response.choices[0].text.strip()
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I apologize, but I encountered an error processing your request. Please try again later."
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((openai.error.APIError, openai.error.Timeout, openai.error.ServiceUnavailableError))
    )
    async def generate_response_async(
        self, 
        prompt: str, 
        max_tokens: int = None, 
        temperature: float = None,
        system: str = None,
        user: str = None,
        assistant: str = None,
        history: List[Dict[str, str]] = None
    ) -> str:
        """
        Generate a response from the language model asynchronously.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            system: System message
            user: User message
            assistant: Assistant message
            history: Conversation history
            
        Returns:
            str: Generated response
        """
        try:
            # Format prompt if components are provided
            if system or user or assistant or history:
                prompt = self._format_prompt(system, user, assistant, history)
            
            # Set parameters
            params = self.default_params.copy()
            if max_tokens:
                params["max_tokens"] = max_tokens
            if temperature is not None:
                params["temperature"] = temperature
            
            # Generate response
            response = await openai.Completion.acreate(
                model=settings.LLM_MODEL,
                prompt=prompt,
                **params
            )
            
            # Extract and return text
            return response.choices[0].text.strip()
        except Exception as e:
            logger.error(f"Error generating response asynchronously: {str(e)}")
            return "I apologize, but I encountered an error processing your request. Please try again later."
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((openai.error.APIError, openai.error.Timeout, openai.error.ServiceUnavailableError))
    )
    def generate_embeddings(self, text: str) -> List[float]:
        """
        Generate embeddings for text.
        
        Args:
            text: Input text
            
        Returns:
            List[float]: Embedding vector
        """
        try:
            # Generate embeddings
            response = openai.Embedding.create(
                model=settings.EMBEDDING_MODEL,
                input=text
            )
            
            # Extract and return embedding
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            return []
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((openai.error.APIError, openai.error.Timeout, openai.error.ServiceUnavailableError))
    )
    async def generate_embeddings_async(self, text: str) -> List[float]:
        """
        Generate embeddings for text asynchronously.
        
        Args:
            text: Input text
            
        Returns:
            List[float]: Embedding vector
        """
        try:
            # Generate embeddings
            response = await openai.Embedding.acreate(
                model=settings.EMBEDDING_MODEL,
                input=text
            )
            
            # Extract and return embedding
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embeddings asynchronously: {str(e)}")
            return []
    
    def _format_prompt(
        self, 
        system: str = None, 
        user: str = None, 
        assistant: str = None, 
        history: List[Dict[str, str]] = None
    ) -> str:
        """
        Format a prompt with system, user, and assistant messages.
        
        Args:
            system: System message
            user: User message
            assistant: Assistant message
            history: Conversation history
            
        Returns:
            str: Formatted prompt
        """
        prompt = ""
        
        # Add system message
        if system:
            prompt += f"System: {system}\n\n"
        
        # Add conversation history
        if history:
            for message in history:
                role = message.get("role", "")
                content = message.get("content", "")
                
                if role.lower() == "system":
                    prompt += f"System: {content}\n\n"
                elif role.lower() == "user":
                    prompt += f"User: {content}\n\n"
                elif role.lower() == "assistant":
                    prompt += f"Assistant: {content}\n\n"
        
        # Add current messages
        if user:
            prompt += f"User: {user}\n\n"
        if assistant:
            prompt += f"Assistant: {assistant}\n\n"
        
        # Add final prompt for assistant
        if not assistant:
            prompt += "Assistant: "
        
        return prompt
    
    def generate_structured_output(
        self, 
        prompt: str, 
        output_schema: Dict[str, Any],
        max_tokens: int = None, 
        temperature: float = None
    ) -> Dict[str, Any]:
        """
        Generate a structured JSON output from the language model.
        
        Args:
            prompt: Input prompt
            output_schema: JSON schema for output
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Dict[str, Any]: Structured output
        """
        try:
            # Create prompt with schema instructions
            schema_str = json.dumps(output_schema, indent=2)
            structured_prompt = f"{prompt}\n\nPlease provide your response in the following JSON format:\n{schema_str}\n\nJSON response:"
            
            # Generate response
            response_text = self.generate_response(
                prompt=structured_prompt,
                max_tokens=max_tokens or 2000,
                temperature=temperature or 0.2
            )
            
            # Extract JSON from response
            try:
                # Find JSON in response
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    return json.loads(json_str)
                else:
                    # Try to parse the whole response as JSON
                    return json.loads(response_text)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from response: {response_text}")
                return {"error": "Failed to generate structured output"}
        except Exception as e:
            logger.error(f"Error generating structured output: {str(e)}")
            return {"error": "An error occurred while generating structured output"}
    
    async def generate_structured_output_async(
        self, 
        prompt: str, 
        output_schema: Dict[str, Any],
        max_tokens: int = None, 
        temperature: float = None
    ) -> Dict[str, Any]:
        """
        Generate a structured JSON output from the language model asynchronously.
        
        Args:
            prompt: Input prompt
            output_schema: JSON schema for output
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Dict[str, Any]: Structured output
        """
        try:
            # Create prompt with schema instructions
            schema_str = json.dumps(output_schema, indent=2)
            structured_prompt = f"{prompt}\n\nPlease provide your response in the following JSON format:\n{schema_str}\n\nJSON response:"
            
            # Generate response
            response_text = await self.generate_response_async(
                prompt=structured_prompt,
                max_tokens=max_tokens or 2000,
                temperature=temperature or 0.2
            )
            
            # Extract JSON from response
            try:
                # Find JSON in response
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    return json.loads(json_str)
                else:
                    # Try to parse the whole response as JSON
                    return json.loads(response_text)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from response: {response_text}")
                return {"error": "Failed to generate structured output"}
        except Exception as e:
            logger.error(f"Error generating structured output asynchronously: {str(e)}")
            return {"error": "An error occurred while generating structured output"}
