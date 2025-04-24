"""
Attorney-General.AI - Memory Condenser

This module implements the memory condenser for the Attorney-General.AI backend.
It provides functionality for condensing and summarizing memory items.
"""

import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from backend.data.models import MemoryItem, Session as ChatSession
from backend.core.llm_service import LLMService
from backend.memory.memory_store import MemoryStore

logger = logging.getLogger(__name__)

class MemoryCondenser:
    """Memory condenser for summarizing and managing memory."""
    
    def __init__(self, db: Session, llm_service: Optional[LLMService] = None, memory_store: Optional[MemoryStore] = None):
        """
        Initialize the memory condenser.
        
        Args:
            db: Database session
            llm_service: Optional LLM service for generating summaries
            memory_store: Optional memory store for accessing memories
        """
        self.db = db
        self.llm_service = llm_service or LLMService()
        self.memory_store = memory_store or MemoryStore(db, self.llm_service)
    
    async def condense_session_memories(self, session_id: str, max_items: int = 10) -> Optional[MemoryItem]:
        """
        Condense short-term memories into a long-term memory summary.
        
        Args:
            session_id: Session ID
            max_items: Maximum number of items to condense
            
        Returns:
            Optional[MemoryItem]: Created summary memory item, or None if no memories to condense
        """
        # Get short-term memories for the session
        memories = self.db.query(MemoryItem).filter(
            MemoryItem.session_id == session_id,
            MemoryItem.memory_type == "short_term"
        ).order_by(
            MemoryItem.importance.desc(),
            MemoryItem.created_at.desc()
        ).limit(max_items).all()
        
        if not memories:
            logger.debug(f"No memories to condense for session: {session_id}")
            return None
        
        # Format memories for summarization
        memory_texts = [f"- {memory.content} (Importance: {memory.importance:.2f})" for memory in memories]
        memories_text = "\n".join(memory_texts)
        
        # Create prompt for summarization
        prompt = f"""
        Summarize the following conversation memories into a concise summary that captures the most important information:
        
        {memories_text}
        
        Provide a concise summary that captures the key points and important details.
        """
        
        # Generate summary
        summary = await self.llm_service.generate_response_async(
            prompt=prompt,
            max_tokens=300,
            temperature=0.5
        )
        
        # Create long-term memory with the summary
        summary_memory = await self.memory_store.add_memory(
            session_id=session_id,
            content=summary,
            importance=0.8,  # High importance for summaries
            memory_type="long_term"
        )
        
        logger.info(f"Created memory summary for session {session_id}: {summary_memory.id}")
        
        return summary_memory
    
    async def should_condense_memories(self, session_id: str, threshold: int = 20) -> bool:
        """
        Determine if memories should be condensed based on count.
        
        Args:
            session_id: Session ID
            threshold: Threshold count for condensing
            
        Returns:
            bool: True if memories should be condensed
        """
        # Count short-term memories
        count = self.db.query(MemoryItem).filter(
            MemoryItem.session_id == session_id,
            MemoryItem.memory_type == "short_term"
        ).count()
        
        return count >= threshold
    
    async def cleanup_old_memories(self, days_old: int = 30) -> int:
        """
        Clean up old short-term memories.
        
        Args:
            days_old: Age in days for memories to be considered old
            
        Returns:
            int: Number of deleted memories
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        # Delete old short-term memories
        result = self.db.query(MemoryItem).filter(
            MemoryItem.memory_type == "short_term",
            MemoryItem.created_at < cutoff_date
        ).delete()
        
        self.db.commit()
        
        logger.info(f"Cleaned up {result} old memory items")
        
        return result
    
    async def generate_session_summary(self, session_id: str) -> str:
        """
        Generate a summary of a session from its memories.
        
        Args:
            session_id: Session ID
            
        Returns:
            str: Session summary
        """
        # Get all memories for the session
        memories = self.db.query(MemoryItem).filter(
            MemoryItem.session_id == session_id
        ).order_by(
            MemoryItem.created_at.asc()
        ).all()
        
        if not memories:
            return "No memories found for this session."
        
        # Format memories for summarization
        memory_texts = [f"- {memory.content}" for memory in memories]
        memories_text = "\n".join(memory_texts)
        
        # Create prompt for summarization
        prompt = f"""
        Generate a comprehensive summary of the following conversation:
        
        {memories_text}
        
        Provide a detailed summary that captures the key points, questions asked, information provided, and conclusions reached.
        """
        
        # Generate summary
        summary = await self.llm_service.generate_response_async(
            prompt=prompt,
            max_tokens=500,
            temperature=0.5
        )
        
        return summary
