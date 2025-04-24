"""
Database integration for Attorney-General.AI.

This module provides database setup, connection management, and initialization functions.
"""

import logging
import os
from typing import Generator, Dict, Any, List
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import uuid
from datetime import datetime

from backend.config.settings import settings
from backend.security.security_system import get_password_hash

# Configure logging
logger = logging.getLogger(__name__)

# Create SQLAlchemy engine
if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite-specific configuration
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
        pool_pre_ping=True,
    )
    
    # Enable foreign key constraints for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    # PostgreSQL or other database configuration
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_recycle=settings.DATABASE_POOL_RECYCLE,
        pool_pre_ping=True,
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """
    Get a database session.
    
    Yields:
        Session: Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db() -> None:
    """
    Initialize the database by creating all tables.
    """
    try:
        # Import models to ensure they are registered with Base
        from backend.data.models import (
            User, Session, Message, Document, DocumentChunk, 
            MemoryItem, Tool, Agent
        )
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

def create_initial_data(db: Session) -> None:
    """
    Create initial data in the database.
    
    Args:
        db: Database session
    """
    try:
        # Import models
        from backend.data.models import User, Tool, Agent
        
        # Check if admin user exists
        admin_user = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
        
        if not admin_user:
            # Create admin user
            admin_user = User(
                id=str(uuid.uuid4()),
                username=settings.ADMIN_USERNAME,
                email=settings.ADMIN_EMAIL,
                hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                full_name="Admin User",
                is_active=True,
                is_admin=True,
                created_at=datetime.utcnow()
            )
            db.add(admin_user)
            logger.info(f"Created admin user: {settings.ADMIN_USERNAME}")
        
        # Check if tools exist
        if db.query(Tool).count() == 0:
            # Create default tools
            tools = [
                Tool(
                    id=str(uuid.uuid4()),
                    name="legal_research",
                    description="Performs legal research on specific topics or questions",
                    enabled=True,
                    created_at=datetime.utcnow()
                ),
                Tool(
                    id=str(uuid.uuid4()),
                    name="document_analysis",
                    description="Analyzes legal documents to extract information and insights",
                    enabled=True,
                    created_at=datetime.utcnow()
                ),
                Tool(
                    id=str(uuid.uuid4()),
                    name="case_law_search",
                    description="Searches for relevant case law based on specific criteria",
                    enabled=True,
                    created_at=datetime.utcnow()
                )
            ]
            
            for tool in tools:
                db.add(tool)
            
            logger.info(f"Created {len(tools)} default tools")
        
        # Check if agents exist
        if db.query(Agent).count() == 0:
            # Create default agents
            agents = [
                Agent(
                    id=str(uuid.uuid4()),
                    name="legal_assistant",
                    description="General legal assistant for answering questions and providing guidance",
                    enabled=True,
                    created_at=datetime.utcnow()
                ),
                Agent(
                    id=str(uuid.uuid4()),
                    name="contract_specialist",
                    description="Specialized agent for contract analysis and drafting assistance",
                    enabled=True,
                    created_at=datetime.utcnow()
                ),
                Agent(
                    id=str(uuid.uuid4()),
                    name="litigation_advisor",
                    description="Specialized agent for litigation strategy and case analysis",
                    enabled=True,
                    created_at=datetime.utcnow()
                )
            ]
            
            for agent in agents:
                db.add(agent)
            
            logger.info(f"Created {len(agents)} default agents")
        
        # Commit changes
        db.commit()
        logger.info("Initial data created successfully")
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating initial data: {str(e)}")
        raise

def get_engine():
    """
    Get the SQLAlchemy engine.
    
    Returns:
        Engine: SQLAlchemy engine
    """
    return engine

def get_session_local():
    """
    Get the SessionLocal factory.
    
    Returns:
        sessionmaker: Session factory
    """
    return SessionLocal
