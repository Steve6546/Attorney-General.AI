"""
Database repository pattern implementation for Attorney-General.AI.

This module provides repository classes for database operations.
"""

import logging
from typing import List, Optional, Dict, Any, Generic, TypeVar, Type
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

from backend.data.models import User, Session as ChatSession, Message, Document, DocumentChunk, MemoryItem, Tool, Agent, AgentTool
from backend.data.database import Base

# Configure logging
logger = logging.getLogger(__name__)

# Generic type for models
T = TypeVar('T', bound=Base)

class BaseRepository(Generic[T]):
    """Base repository for database operations."""
    
    def __init__(self, db: Session, model: Type[T]):
        """
        Initialize the repository.
        
        Args:
            db: Database session
            model: Model class
        """
        self.db = db
        self.model = model
    
    def get_by_id(self, id: str) -> Optional[T]:
        """
        Get an entity by ID.
        
        Args:
            id: Entity ID
            
        Returns:
            Optional[T]: Entity if found, None otherwise
        """
        try:
            return self.db.query(self.model).filter(self.model.id == id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model.__name__} by ID: {str(e)}")
            return None
    
    def get_all(self) -> List[T]:
        """
        Get all entities.
        
        Returns:
            List[T]: List of entities
        """
        try:
            return self.db.query(self.model).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting all {self.model.__name__}: {str(e)}")
            return []
    
    def create(self, entity: T) -> Optional[T]:
        """
        Create a new entity.
        
        Args:
            entity: Entity to create
            
        Returns:
            Optional[T]: Created entity if successful, None otherwise
        """
        try:
            self.db.add(entity)
            self.db.commit()
            self.db.refresh(entity)
            return entity
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating {self.model.__name__}: {str(e)}")
            return None
    
    def update(self, entity: T) -> Optional[T]:
        """
        Update an entity.
        
        Args:
            entity: Entity to update
            
        Returns:
            Optional[T]: Updated entity if successful, None otherwise
        """
        try:
            self.db.add(entity)
            self.db.commit()
            self.db.refresh(entity)
            return entity
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating {self.model.__name__}: {str(e)}")
            return None
    
    def delete(self, id: str) -> bool:
        """
        Delete an entity by ID.
        
        Args:
            id: Entity ID
            
        Returns:
            bool: True if deleted, False otherwise
        """
        try:
            entity = self.get_by_id(id)
            if entity:
                self.db.delete(entity)
                self.db.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting {self.model.__name__}: {str(e)}")
            return False


class UserRepository(BaseRepository[User]):
    """Repository for User operations."""
    
    def __init__(self, db: Session):
        """
        Initialize the repository.
        
        Args:
            db: Database session
        """
        super().__init__(db, User)
    
    def get_by_username(self, username: str) -> Optional[User]:
        """
        Get a user by username.
        
        Args:
            username: Username
            
        Returns:
            Optional[User]: User if found, None otherwise
        """
        try:
            return self.db.query(User).filter(User.username == username).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting user by username: {str(e)}")
            return None
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email.
        
        Args:
            email: Email
            
        Returns:
            Optional[User]: User if found, None otherwise
        """
        try:
            return self.db.query(User).filter(User.email == email).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting user by email: {str(e)}")
            return None
    
    def update_last_login(self, user_id: str) -> bool:
        """
        Update a user's last login time.
        
        Args:
            user_id: User ID
            
        Returns:
            bool: True if updated, False otherwise
        """
        try:
            user = self.get_by_id(user_id)
            if user:
                user.last_login = datetime.utcnow()
                self.db.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating user last login: {str(e)}")
            return False


class SessionRepository(BaseRepository[ChatSession]):
    """Repository for Session operations."""
    
    def __init__(self, db: Session):
        """
        Initialize the repository.
        
        Args:
            db: Database session
        """
        super().__init__(db, ChatSession)
    
    def get_by_user_id(self, user_id: str) -> List[ChatSession]:
        """
        Get all sessions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List[ChatSession]: List of sessions
        """
        try:
            return self.db.query(ChatSession).filter(
                ChatSession.user_id == user_id
            ).order_by(ChatSession.updated_at.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting sessions by user ID: {str(e)}")
            return []
    
    def get_active_by_user_id(self, user_id: str) -> List[ChatSession]:
        """
        Get active sessions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List[ChatSession]: List of active sessions
        """
        try:
            return self.db.query(ChatSession).filter(
                ChatSession.user_id == user_id,
                ChatSession.is_active == True
            ).order_by(ChatSession.updated_at.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting active sessions by user ID: {str(e)}")
            return []
    
    def update_session_activity(self, session_id: str, is_active: bool) -> bool:
        """
        Update a session's activity status.
        
        Args:
            session_id: Session ID
            is_active: Activity status
            
        Returns:
            bool: True if updated, False otherwise
        """
        try:
            session = self.get_by_id(session_id)
            if session:
                session.is_active = is_active
                session.updated_at = datetime.utcnow()
                self.db.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating session activity: {str(e)}")
            return False


class MessageRepository(BaseRepository[Message]):
    """Repository for Message operations."""
    
    def __init__(self, db: Session):
        """
        Initialize the repository.
        
        Args:
            db: Database session
        """
        super().__init__(db, Message)
    
    def get_by_session_id(self, session_id: str) -> List[Message]:
        """
        Get all messages for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List[Message]: List of messages
        """
        try:
            return self.db.query(Message).filter(
                Message.session_id == session_id
            ).order_by(Message.created_at.asc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting messages by session ID: {str(e)}")
            return []
    
    def get_by_role(self, session_id: str, role: str) -> List[Message]:
        """
        Get messages by role for a session.
        
        Args:
            session_id: Session ID
            role: Message role
            
        Returns:
            List[Message]: List of messages
        """
        try:
            return self.db.query(Message).filter(
                Message.session_id == session_id,
                Message.role == role
            ).order_by(Message.created_at.asc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting messages by role: {str(e)}")
            return []
    
    def get_latest(self, session_id: str, limit: int = 10) -> List[Message]:
        """
        Get latest messages for a session.
        
        Args:
            session_id: Session ID
            limit: Maximum number of messages
            
        Returns:
            List[Message]: List of messages
        """
        try:
            return self.db.query(Message).filter(
                Message.session_id == session_id
            ).order_by(Message.created_at.desc()).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting latest messages: {str(e)}")
            return []


class DocumentRepository(BaseRepository[Document]):
    """Repository for Document operations."""
    
    def __init__(self, db: Session):
        """
        Initialize the repository.
        
        Args:
            db: Database session
        """
        super().__init__(db, Document)
    
    def get_by_user_id(self, user_id: str) -> List[Document]:
        """
        Get all documents for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List[Document]: List of documents
        """
        try:
            return self.db.query(Document).filter(
                Document.user_id == user_id
            ).order_by(Document.uploaded_at.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting documents by user ID: {str(e)}")
            return []
    
    def get_processed(self, user_id: str) -> List[Document]:
        """
        Get processed documents for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List[Document]: List of processed documents
        """
        try:
            return self.db.query(Document).filter(
                Document.user_id == user_id,
                Document.processed == True
            ).order_by(Document.uploaded_at.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting processed documents: {str(e)}")
            return []
    
    def update_processed_status(self, document_id: str, processed: bool) -> bool:
        """
        Update a document's processed status.
        
        Args:
            document_id: Document ID
            processed: Processed status
            
        Returns:
            bool: True if updated, False otherwise
        """
        try:
            document = self.get_by_id(document_id)
            if document:
                document.processed = processed
                self.db.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating document processed status: {str(e)}")
            return False


class DocumentChunkRepository(BaseRepository[DocumentChunk]):
    """Repository for DocumentChunk operations."""
    
    def __init__(self, db: Session):
        """
        Initialize the repository.
        
        Args:
            db: Database session
        """
        super().__init__(db, DocumentChunk)
    
    def get_by_document_id(self, document_id: str) -> List[DocumentChunk]:
        """
        Get all chunks for a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            List[DocumentChunk]: List of document chunks
        """
        try:
            return self.db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).order_by(DocumentChunk.chunk_index.asc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting chunks by document ID: {str(e)}")
            return []
    
    def delete_by_document_id(self, document_id: str) -> bool:
        """
        Delete all chunks for a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            bool: True if deleted, False otherwise
        """
        try:
            self.db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).delete()
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting chunks by document ID: {str(e)}")
            return False


class MemoryItemRepository(BaseRepository[MemoryItem]):
    """Repository for MemoryItem operations."""
    
    def __init__(self, db: Session):
        """
        Initialize the repository.
        
        Args:
            db: Database session
        """
        super().__init__(db, MemoryItem)
    
    def get_by_session_id(self, session_id: str) -> List[MemoryItem]:
        """
        Get all memory items for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List[MemoryItem]: List of memory items
        """
        try:
            return self.db.query(MemoryItem).filter(
                MemoryItem.session_id == session_id
            ).order_by(MemoryItem.created_at.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting memory items by session ID: {str(e)}")
            return []
    
    def get_by_memory_type(self, session_id: str, memory_type: str) -> List[MemoryItem]:
        """
        Get memory items by type for a session.
        
        Args:
            session_id: Session ID
            memory_type: Memory type
            
        Returns:
            List[MemoryItem]: List of memory items
        """
        try:
            return self.db.query(MemoryItem).filter(
                MemoryItem.session_id == session_id,
                MemoryItem.memory_type == memory_type
            ).order_by(MemoryItem.created_at.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting memory items by type: {str(e)}")
            return []
    
    def update_access_count(self, memory_id: str) -> bool:
        """
        Update a memory item's access count.
        
        Args:
            memory_id: Memory item ID
            
        Returns:
            bool: True if updated, False otherwise
        """
        try:
            memory = self.get_by_id(memory_id)
            if memory:
                memory.access_count += 1
                memory.last_accessed = datetime.utcnow()
                self.db.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating memory access count: {str(e)}")
            return False
    
    def update_memory_type(self, memory_id: str, memory_type: str) -> bool:
        """
        Update a memory item's type.
        
        Args:
            memory_id: Memory item ID
            memory_type: Memory type
            
        Returns:
            bool: True if updated, False otherwise
        """
        try:
            memory = self.get_by_id(memory_id)
            if memory:
                memory.memory_type = memory_type
                self.db.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating memory type: {str(e)}")
            return False
