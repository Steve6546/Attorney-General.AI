"""
Attorney-General.AI - API Endpoints

This module defines the API endpoints for the Attorney-General.AI backend.
It provides RESTful API routes for interacting with the system.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import uuid
from datetime import datetime, timedelta

from backend.data.database import get_db
from backend.data.models import User, Session as ChatSession, Message, Document
from backend.security.security_system import (
    authenticate_user, create_access_token, get_current_user, 
    get_current_active_user, get_password_hash
)
from backend.core.session_manager import SessionManager
from backend.core.rag_system import RAGSystem
from backend.agenthub.legal_agent.agent import LegalAgent
from backend.tools.legal_research_tool import LegalResearchTool
from backend.tools.document_analysis_tool import DocumentAnalysisTool
from backend.config.settings import settings

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix=settings.API_PREFIX)

# Session manager instance
session_manager = None

# Helper function to get session manager
def get_session_manager(db: Session = Depends(get_db)):
    global session_manager
    if session_manager is None:
        session_manager = SessionManager(db)
    return session_manager

# Authentication endpoints
@router.post("/auth/token", response_model=Dict[str, Any])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Get an access token for authentication.
    
    Args:
        form_data: OAuth2 password request form
        db: Database session
        
    Returns:
        Dict[str, Any]: Access token and token type
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/auth/register", response_model=Dict[str, Any])
async def register_user(
    username: str = Body(...),
    email: str = Body(...),
    password: str = Body(...),
    full_name: str = Body(None),
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    
    Args:
        username: Username
        email: Email
        password: Password
        full_name: Optional full name
        db: Database session
        
    Returns:
        Dict[str, Any]: User information
    """
    # Check if username exists
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email exists
    existing_email = db.query(User).filter(User.email == email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(password)
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        full_name=full_name
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active
    }

@router.get("/auth/me", response_model=Dict[str, Any])
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get current user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: User information
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "is_admin": current_user.is_admin
    }

# Session endpoints
@router.post("/sessions", response_model=Dict[str, Any])
async def create_session(
    title: str = Body(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Create a new chat session.
    
    Args:
        title: Optional session title
        current_user: Current authenticated user
        db: Database session
        session_manager: Session manager
        
    Returns:
        Dict[str, Any]: Session information
    """
    session = await session_manager.create_session(current_user.id, title)
    
    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "is_active": session.is_active
    }

@router.get("/sessions", response_model=List[Dict[str, Any]])
async def get_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all sessions for the current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[Dict[str, Any]]: Session information
    """
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.updated_at.desc()).all()
    
    return [
        {
            "id": session.id,
            "title": session.title,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "is_active": session.is_active,
            "message_count": db.query(Message).filter(Message.session_id == session.id).count()
        }
        for session in sessions
    ]

@router.get("/sessions/{session_id}", response_model=Dict[str, Any])
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific session.
    
    Args:
        session_id: Session ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dict[str, Any]: Session information
    """
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    messages = db.query(Message).filter(
        Message.session_id == session_id
    ).order_by(Message.created_at.asc()).all()
    
    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "is_active": session.is_active,
        "messages": [
            {
                "id": message.id,
                "role": message.role,
                "content": message.content,
                "created_at": message.created_at.isoformat()
            }
            for message in messages
        ]
    }

@router.delete("/sessions/{session_id}", response_model=Dict[str, Any])
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Delete a session.
    
    Args:
        session_id: Session ID
        current_user: Current authenticated user
        db: Database session
        session_manager: Session manager
        
    Returns:
        Dict[str, Any]: Result
    """
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    await session_manager.delete_session(session_id)
    
    return {"success": True, "message": "Session deleted"}

# Message endpoints
@router.post("/sessions/{session_id}/messages", response_model=Dict[str, Any])
async def create_message(
    session_id: str,
    content: str = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Create a new message in a session.
    
    Args:
        session_id: Session ID
        content: Message content
        current_user: Current authenticated user
        db: Database session
        session_manager: Session manager
        
    Returns:
        Dict[str, Any]: Message information and response
    """
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Create user message
    user_message = Message(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="user",
        content=content
    )
    
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    # Get agent response
    agent = await session_manager.get_agent(session_id)
    response = await agent.process_message(content)
    
    # Create assistant message
    assistant_message = Message(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="assistant",
        content=response
    )
    
    db.add(assistant_message)
    
    # Update session
    session.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(assistant_message)
    
    return {
        "user_message": {
            "id": user_message.id,
            "role": user_message.role,
            "content": user_message.content,
            "created_at": user_message.created_at.isoformat()
        },
        "assistant_message": {
            "id": assistant_message.id,
            "role": assistant_message.role,
            "content": assistant_message.content,
            "created_at": assistant_message.created_at.isoformat()
        }
    }

# Document endpoints
@router.post("/documents", response_model=Dict[str, Any])
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload a document.
    
    Args:
        file: Uploaded file
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dict[str, Any]: Document information
    """
    # Create storage directory if it doesn't exist
    os.makedirs(settings.UPLOADS_PATH, exist_ok=True)
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    filename = file.filename
    file_extension = os.path.splitext(filename)[1]
    storage_filename = f"{file_id}{file_extension}"
    file_path = os.path.join(settings.UPLOADS_PATH, storage_filename)
    
    # Save file
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Create document record
    document = Document(
        id=file_id,
        user_id=current_user.id,
        filename=filename,
        file_path=file_path,
        content_type=file.content_type,
        size=len(content),
        processed=False
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    return {
        "id": document.id,
        "filename": document.filename,
        "content_type": document.content_type,
        "size": document.size,
        "uploaded_at": document.uploaded_at.isoformat(),
        "processed": document.processed
    }

@router.get("/documents", response_model=List[Dict[str, Any]])
async def get_documents(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all documents for the current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[Dict[str, Any]]: Document information
    """
    documents = db.query(Document).filter(
        Document.user_id == current_user.id
    ).order_by(Document.uploaded_at.desc()).all()
    
    return [
        {
            "id": document.id,
            "filename": document.filename,
            "content_type": document.content_type,
            "size": document.size,
            "uploaded_at": document.uploaded_at.isoformat(),
            "processed": document.processed
        }
        for document in documents
    ]

@router.post("/documents/{document_id}/index", response_model=Dict[str, Any])
async def index_document(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Index a document for RAG.
    
    Args:
        document_id: Document ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dict[str, Any]: Indexing result
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Index document
    rag_system = RAGSystem(db)
    result = await rag_system.index_document(document_id)
    
    return result

# Legal research endpoints
@router.post("/legal-research", response_model=Dict[str, Any])
async def perform_legal_research(
    query: str = Body(...),
    jurisdiction: str = Body(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Perform legal research.
    
    Args:
        query: Research query
        jurisdiction: Optional jurisdiction
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dict[str, Any]: Research results
    """
    # Create legal research tool
    legal_research_tool = LegalResearchTool()
    
    # Perform research
    result = await legal_research_tool.run(
        query=query,
        jurisdiction=jurisdiction
    )
    
    return result

# Document analysis endpoints
@router.post("/document-analysis", response_model=Dict[str, Any])
async def analyze_document(
    document_id: str = Body(...),
    analysis_type: str = Body("summary"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Analyze a document.
    
    Args:
        document_id: Document ID
        analysis_type: Analysis type
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dict[str, Any]: Analysis results
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Create document analysis tool
    document_analysis_tool = DocumentAnalysisTool()
    
    # Analyze document
    result = await document_analysis_tool.run(
        document_id=document_id,
        analysis_type=analysis_type
    )
    
    return result

# RAG endpoints
@router.post("/rag/query", response_model=Dict[str, Any])
async def rag_query(
    query: str = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Query the RAG system.
    
    Args:
        query: Query text
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dict[str, Any]: Query results
    """
    # Create RAG system
    rag_system = RAGSystem(db)
    
    # Generate augmented response
    result = await rag_system.generate_augmented_response(query)
    
    return result
