"""
Attorney-General.AI - Memory Store

This module implements the memory system for the Attorney-General.AI backend.
It provides functionality for storing and retrieving memory items.
"""

import logging
from typing import Dict, Any, List, Optional
import asyncio
import uuid
import json
import time
from datetime import datetime

logger = logging.getLogger(__name__)

class MemoryStore:
    """Memory store for short-term and long-term memory."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the memory store.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.short_term_memory = {}  # Session-based short-term memory
        self.long_term_memory = {}   # Persistent long-term memory
        self.max_short_term_items = self.config.get("max_short_term_items", 100)
        self.max_long_term_items = self.config.get("max_long_term_items", 1000)
    
    async def add_to_short_term(self, session_id: str, key: str, value: Any) -> None:
        """
        Add an item to short-term memory.
        
        Args:
            session_id: The session ID
            key: The memory item key
            value: The memory item value
        """
        if session_id not in self.short_term_memory:
            self.short_term_memory[session_id] = {}
        
        # Add timestamp to the memory item
        memory_item = {
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
        
        self.short_term_memory[session_id][key] = memory_item
        
        # Limit the number of items per session
        if len(self.short_term_memory[session_id]) > self.max_short_term_items:
            # Remove oldest items
            sorted_items = sorted(
                self.short_term_memory[session_id].items(),
                key=lambda x: x[1]["timestamp"]
            )
            
            # Keep only the newest items
            self.short_term_memory[session_id] = dict(sorted_items[-self.max_short_term_items:])
    
    async def get_from_short_term(self, session_id: str, key: str) -> Optional[Any]:
        """
        Get an item from short-term memory.
        
        Args:
            session_id: The session ID
            key: The memory item key
            
        Returns:
            Optional[Any]: The memory item value or None if not found
        """
        if session_id in self.short_term_memory and key in self.short_term_memory[session_id]:
            return self.short_term_memory[session_id][key]["value"]
        
        return None
    
    async def get_all_short_term(self, session_id: str) -> Dict[str, Any]:
        """
        Get all short-term memory items for a session.
        
        Args:
            session_id: The session ID
            
        Returns:
            Dict[str, Any]: Dictionary of memory items
        """
        if session_id in self.short_term_memory:
            # Return only the values, not the metadata
            return {
                key: item["value"] 
                for key, item in self.short_term_memory[session_id].items()
            }
        
        return {}
    
    async def add_to_long_term(self, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Add an item to long-term memory.
        
        Args:
            key: The memory item key
            value: The memory item value
            metadata: Optional metadata for the memory item
            
        Returns:
            str: The memory item ID
        """
        memory_id = str(uuid.uuid4())
        
        # Add timestamp and metadata to the memory item
        memory_item = {
            "id": memory_id,
            "key": key,
            "value": value,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        
        self.long_term_memory[memory_id] = memory_item
        
        # Limit the total number of items
        if len(self.long_term_memory) > self.max_long_term_items:
            # Remove oldest items
            sorted_items = sorted(
                self.long_term_memory.items(),
                key=lambda x: x[1]["timestamp"]
            )
            
            # Keep only the newest items
            self.long_term_memory = dict(sorted_items[-self.max_long_term_items:])
        
        return memory_id
    
    async def get_from_long_term(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an item from long-term memory by ID.
        
        Args:
            memory_id: The memory item ID
            
        Returns:
            Optional[Dict[str, Any]]: The memory item or None if not found
        """
        return self.long_term_memory.get(memory_id)
    
    async def search_long_term(self, query: str, metadata_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search long-term memory.
        
        Args:
            query: The search query
            metadata_filter: Optional metadata filter
            
        Returns:
            List[Dict[str, Any]]: List of matching memory items
        """
        results = []
        
        for item in self.long_term_memory.values():
            # Check if the query matches the key or value
            key_match = query.lower() in item["key"].lower()
            value_match = False
            
            # Check if value is string and contains query
            if isinstance(item["value"], str):
                value_match = query.lower() in item["value"].lower()
            elif isinstance(item["value"], dict):
                # Try to match in JSON string representation
                try:
                    value_str = json.dumps(item["value"])
                    value_match = query.lower() in value_str.lower()
                except:
                    pass
            
            # Check metadata filter if provided
            metadata_match = True
            if metadata_filter:
                for k, v in metadata_filter.items():
                    if k not in item["metadata"] or item["metadata"][k] != v:
                        metadata_match = False
                        break
            
            if (key_match or value_match) and metadata_match:
                results.append(item)
        
        return results
    
    async def clear_short_term(self, session_id: str) -> None:
        """
        Clear all short-term memory for a session.
        
        Args:
            session_id: The session ID
        """
        if session_id in self.short_term_memory:
            del self.short_term_memory[session_id]
    
    async def clear_all_short_term(self) -> None:
        """Clear all short-term memory."""
        self.short_term_memory = {}
    
    async def clear_long_term(self) -> None:
        """Clear all long-term memory."""
        self.long_term_memory = {}
