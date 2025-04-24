"""
Attorney-General.AI - Base Agent

This module defines the base agent class for the Attorney-General.AI backend.
It provides the foundation for specialized agents like the legal agent.
"""

import logging
from typing import Dict, Any, List, Optional, Union
import uuid
import json
from datetime import datetime

from backend.core.llm_service import LLMService
from backend.memory.memory_store import MemoryStore
from backend.utils.prompt_loader import load_prompt
from backend.tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class BaseAgent:
    """Base agent class for Attorney-General.AI."""
    
    def __init__(
        self,
        session_id: str,
        llm_service: Optional[LLMService] = None,
        memory_store: Optional[MemoryStore] = None,
        tools: Optional[List[BaseTool]] = None,
        system_prompt: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the base agent.
        
        Args:
            session_id: Session ID for the agent
            llm_service: Optional LLM service
            memory_store: Optional memory store
            tools: Optional list of tools
            system_prompt: Optional system prompt
            config: Optional configuration
        """
        self.session_id = session_id
        self.llm_service = llm_service or LLMService()
        self.memory_store = memory_store
        self.tools = tools or []
        self.system_prompt = system_prompt
        self.config = config or {}
        
        # Initialize agent state
        self.conversation_history = []
        self.last_response = None
        self.metadata = {}
    
    async def process_message(self, message: str) -> str:
        """
        Process a user message and generate a response.
        
        Args:
            message: User message
            
        Returns:
            str: Agent response
        """
        # Add message to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Store in memory if memory store is available
        if self.memory_store:
            await self.memory_store.add_memory(
                session_id=self.session_id,
                content=f"User: {message}",
                importance=0.5,
                memory_type="short_term"
            )
        
        # Process message
        response = await self._generate_response(message)
        
        # Add response to conversation history
        self.conversation_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Store in memory if memory store is available
        if self.memory_store:
            await self.memory_store.add_memory(
                session_id=self.session_id,
                content=f"Assistant: {response}",
                importance=0.5,
                memory_type="short_term"
            )
        
        self.last_response = response
        return response
    
    async def _generate_response(self, message: str) -> str:
        """
        Generate a response to a user message.
        
        Args:
            message: User message
            
        Returns:
            str: Generated response
        """
        # This is a basic implementation that should be overridden by subclasses
        prompt = self._build_prompt(message)
        
        response = await self.llm_service.generate_response_async(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.7,
            system_message=self.system_prompt
        )
        
        return response
    
    def _build_prompt(self, message: str) -> str:
        """
        Build a prompt for the LLM.
        
        Args:
            message: User message
            
        Returns:
            str: Prompt for the LLM
        """
        # This is a basic implementation that should be overridden by subclasses
        history_text = ""
        
        # Include relevant conversation history
        for item in self.conversation_history[-10:]:  # Last 10 messages
            role = item["role"]
            content = item["content"]
            history_text += f"{role.capitalize()}: {content}\n\n"
        
        prompt = f"{history_text}User: {message}\n\nAssistant:"
        return prompt
    
    async def get_relevant_memories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get relevant memories for a query.
        
        Args:
            query: Query text
            limit: Maximum number of memories to return
            
        Returns:
            List[Dict[str, Any]]: Relevant memories
        """
        if not self.memory_store:
            return []
        
        memory_items = await self.memory_store.get_relevant_memories(
            session_id=self.session_id,
            query=query,
            limit=limit
        )
        
        return [
            {
                "id": item.id,
                "content": item.content,
                "importance": item.importance,
                "created_at": item.created_at.isoformat(),
                "memory_type": item.memory_type
            }
            for item in memory_items
        ]
    
    async def use_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Use a tool.
        
        Args:
            tool_name: Name of the tool to use
            **kwargs: Tool parameters
            
        Returns:
            Dict[str, Any]: Tool result
            
        Raises:
            ValueError: If tool not found
        """
        # Find the tool
        tool = next((t for t in self.tools if t.name == tool_name), None)
        
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")
        
        # Use the tool
        result = await tool.run(**kwargs)
        
        # Log tool usage
        logger.info(f"Agent used tool: {tool_name}")
        
        return result
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        Get available tools.
        
        Returns:
            List[Dict[str, Any]]: Available tools
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in self.tools
        ]
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """
        Get conversation history.
        
        Returns:
            List[Dict[str, Any]]: Conversation history
        """
        return self.conversation_history
    
    def clear_conversation_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []
        self.last_response = None
