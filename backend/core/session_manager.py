"""
Attorney-General.AI - Session Manager

This module implements the session manager for the Attorney-General.AI backend.
It provides functionality for creating, managing, and retrieving chat sessions.
"""

import logging
from typing import Dict, Any, List, Optional, Union
import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from backend.data.models import User, Session as ChatSession, Message
from backend.agenthub.legal_agent.agent import LegalAgent
from backend.tools.legal_research_tool import LegalResearchTool
from backend.tools.document_analysis_tool import DocumentAnalysisTool
from backend.memory.memory_store import MemoryStore
from backend.core.llm_service import LLMService

logger = logging.getLogger(__name__)

class SessionManager:
    """Session manager for chat sessions."""
    
    def __init__(self, db: Session):
        """
        Initialize the session manager.
        
        Args:
            db: Database session
        """
        self.db = db
        self.active_agents = {}
        self.llm_service = LLMService()
    
    async def create_session(self, user_id: str, title: Optional[str] = None) -> ChatSession:
        """
        Create a new chat session.
        
        Args:
            user_id: User ID
            title: Optional session title
            
        Returns:
            ChatSession: Created session
        """
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Create session
        session = ChatSession(
            id=session_id,
            user_id=user_id,
            title=title or "New Session",
            is_active=True
        )
        
        # Add to database
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        logger.info(f"Created session {session_id} for user {user_id}")
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        """
        Get a session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            Optional[ChatSession]: Session if found, None otherwise
        """
        return self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
    
    async def get_agent(self, session_id: str) -> LegalAgent:
        """
        Get or create an agent for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            LegalAgent: Agent for the session
            
        Raises:
            ValueError: If session not found
        """
        # Check if agent already exists
        if session_id in self.active_agents:
            return self.active_agents[session_id]
        
        # Get session
        session = await self.get_session(session_id)
        
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        # Create memory store
        memory_store = MemoryStore(self.db, self.llm_service)
        
        # Create tools
        tools = [
            LegalResearchTool(self.llm_service),
            DocumentAnalysisTool(self.llm_service)
        ]
        
        # Create agent
        agent = LegalAgent(
            session_id=session_id,
            llm_service=self.llm_service,
            memory_store=memory_store,
            tools=tools
        )
        
        # Store agent
        self.active_agents[session_id] = agent
        
        logger.info(f"Created agent for session {session_id}")
        
        return agent
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        # Get session
        session = await self.get_session(session_id)
        
        if not session:
            return False
        
        # Delete messages
        self.db.query(Message).filter(Message.session_id == session_id).delete()
        
        # Delete session
        self.db.delete(session)
        self.db.commit()
        
        # Remove agent if exists
        if session_id in self.active_agents:
            del self.active_agents[session_id]
        
        logger.info(f"Deleted session {session_id}")
        
        return True
    
    async def get_user_sessions(self, user_id: str) -> List[ChatSession]:
        """
        Get all sessions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List[ChatSession]: User sessions
        """
        return self.db.query(ChatSession).filter(
            ChatSession.user_id == user_id
        ).order_by(ChatSession.updated_at.desc()).all()
    
    async def update_session_title(self, session_id: str, title: str) -> Optional[ChatSession]:
        """
        Update a session title.
        
        Args:
            session_id: Session ID
            title: New title
            
        Returns:
            Optional[ChatSession]: Updated session, or None if not found
        """
        # Get session
        session = await self.get_session(session_id)
        
        if not session:
            return None
        
        # Update title
        session.title = title
        session.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(session)
        
        logger.info(f"Updated title for session {session_id}")
        
        return session
    
    async def get_session_messages(self, session_id: str) -> List[Message]:
        """
        Get all messages for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List[Message]: Session messages
        """
        return self.db.query(Message).filter(
            Message.session_id == session_id
        ).order_by(Message.created_at.asc()).all()
    
    def cleanup_inactive_agents(self, max_inactive_time: int = 3600) -> int:
        """
        Clean up inactive agents.
        
        Args:
            max_inactive_time: Maximum inactive time in seconds
            
        Returns:
            int: Number of agents cleaned up
        """
        # Get current time
        now = datetime.utcnow()
        
        # Find inactive sessions
        inactive_sessions = self.db.query(ChatSession).filter(
            (now - ChatSession.updated_at).total_seconds() > max_inactive_time
        ).all()
        
        # Get session IDs
        inactive_session_ids = [session.id for session in inactive_sessions]
        
        # Remove agents
        count = 0
        for session_id in list(self.active_agents.keys()):
            if session_id in inactive_session_ids:
                del self.active_agents[session_id]
                count += 1
        
        logger.info(f"Cleaned up {count} inactive agents")
        
        return count
