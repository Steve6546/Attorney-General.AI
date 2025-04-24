"""
Attorney-General.AI - Memory Store

This module implements the memory system for the Attorney-General.AI backend.
It provides functionality for storing, retrieving, and managing memory items.
"""

import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import json
import numpy as np
from sqlalchemy.orm import Session

from backend.data.models import MemoryItem, Session as ChatSession
from backend.core.llm_service import LLMService

logger = logging.getLogger(__name__)

class MemoryStore:
    """Memory store for managing agent memory."""
    
    def __init__(self, db: Session, llm_service: Optional[LLMService] = None):
        """
        Initialize the memory store.
        
        Args:
            db: Database session
            llm_service: Optional LLM service for generating embeddings
        """
        self.db = db
        self.llm_service = llm_service or LLMService()
    
    async def add_memory(
        self, 
        session_id: str, 
        content: str, 
        importance: float = 0.5,
        memory_type: str = "short_term"
    ) -> MemoryItem:
        """
        Add a memory item.
        
        Args:
            session_id: Session ID
            content: Memory content
            importance: Importance score (0.0 to 1.0)
            memory_type: Memory type ('short_term' or 'long_term')
            
        Returns:
            MemoryItem: Created memory item
        """
        # Generate embedding
        embedding = await self.llm_service.generate_embeddings_async(content)
        
        # Create memory item
        memory_item = MemoryItem(
            session_id=session_id,
            content=content,
            importance=importance,
            embedding=embedding,
            memory_type=memory_type
        )
        
        # Add to database
        self.db.add(memory_item)
        self.db.commit()
        self.db.refresh(memory_item)
        
        logger.debug(f"Added memory item: {memory_item.id}")
        
        return memory_item
    
    async def get_relevant_memories(
        self, 
        session_id: str, 
        query: str, 
        limit: int = 5,
        memory_type: Optional[str] = None
    ) -> List[MemoryItem]:
        """
        Get relevant memories for a query.
        
        Args:
            session_id: Session ID
            query: Query text
            limit: Maximum number of memories to return
            memory_type: Optional memory type filter
            
        Returns:
            List[MemoryItem]: Relevant memory items
        """
        # Generate query embedding
        query_embedding = await self.llm_service.generate_embeddings_async(query)
        
        # Get all memory items for the session
        query = self.db.query(MemoryItem).filter(MemoryItem.session_id == session_id)
        
        if memory_type:
            query = query.filter(MemoryItem.memory_type == memory_type)
        
        memory_items = query.all()
        
        if not memory_items:
            return []
        
        # Calculate similarity scores
        similarities = []
        for item in memory_items:
            if item.embedding:
                # Calculate cosine similarity
                similarity = self._calculate_similarity(query_embedding, item.embedding)
                similarities.append((item, similarity))
            else:
                similarities.append((item, 0.0))
        
        # Sort by similarity and take top results
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_memories = [item for item, _ in similarities[:limit]]
        
        # Update access count and last accessed time
        for item in top_memories:
            item.access_count += 1
            item.last_accessed = datetime.utcnow()
        
        self.db.commit()
        
        return top_memories
    
    def get_all_memories(
        self, 
        session_id: str,
        memory_type: Optional[str] = None
    ) -> List[MemoryItem]:
        """
        Get all memories for a session.
        
        Args:
            session_id: Session ID
            memory_type: Optional memory type filter
            
        Returns:
            List[MemoryItem]: Memory items
        """
        query = self.db.query(MemoryItem).filter(MemoryItem.session_id == session_id)
        
        if memory_type:
            query = query.filter(MemoryItem.memory_type == memory_type)
        
        return query.order_by(MemoryItem.created_at.desc()).all()
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory item.
        
        Args:
            memory_id: Memory item ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        memory_item = self.db.query(MemoryItem).filter(MemoryItem.id == memory_id).first()
        
        if not memory_item:
            return False
        
        self.db.delete(memory_item)
        self.db.commit()
        
        logger.debug(f"Deleted memory item: {memory_id}")
        
        return True
    
    def clear_session_memories(self, session_id: str) -> int:
        """
        Clear all memories for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            int: Number of deleted items
        """
        result = self.db.query(MemoryItem).filter(MemoryItem.session_id == session_id).delete()
        self.db.commit()
        
        logger.debug(f"Cleared {result} memory items for session: {session_id}")
        
        return result
    
    async def promote_to_long_term(self, memory_id: str) -> Optional[MemoryItem]:
        """
        Promote a memory item to long-term memory.
        
        Args:
            memory_id: Memory item ID
            
        Returns:
            Optional[MemoryItem]: Updated memory item, or None if not found
        """
        memory_item = self.db.query(MemoryItem).filter(MemoryItem.id == memory_id).first()
        
        if not memory_item:
            return None
        
        memory_item.memory_type = "long_term"
        memory_item.importance = max(memory_item.importance, 0.7)  # Ensure high importance
        
        self.db.commit()
        self.db.refresh(memory_item)
        
        logger.debug(f"Promoted memory item to long-term: {memory_id}")
        
        return memory_item
    
    def _calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            float: Cosine similarity (-1.0 to 1.0)
        """
        # Convert to numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
