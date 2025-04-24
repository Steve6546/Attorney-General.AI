"""
Attorney-General.AI - API Endpoints

This module defines the API endpoints for the Attorney-General.AI backend.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel
import uuid

from backend.core.llm_service import LLMService
from backend.core.session_manager import SessionManager
from backend.agenthub.legal_agent.agent import LegalAgent

# Define API models
class ChatMessage(BaseModel):
    """Model for chat messages."""
    content: str
    role: str = "user"
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    """Model for chat response."""
    content: str
    session_id: str
    message_id: str

class HistoryResponse(BaseModel):
    """Model for chat history response."""
    messages: List[dict]
    session_id: str

# Create router
router = APIRouter()

# Initialize services
llm_service = LLMService()
session_manager = SessionManager()
legal_agent = LegalAgent()

@router.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage, background_tasks: BackgroundTasks):
    """
    Process a new chat message and return a response.
    
    Args:
        message: The chat message from the user
        background_tasks: FastAPI background tasks
        
    Returns:
        ChatResponse: The AI response
    """
    # Create a new session if none exists
    if not message.session_id:
        message.session_id = str(uuid.uuid4())
    
    # Save the user message
    await session_manager.save_message(
        session_id=message.session_id,
        content=message.content,
        role="user"
    )
    
    # Process the message with the legal agent
    response = await legal_agent.process_request({
        "query": message.content,
        "session_id": message.session_id
    })
    
    # Generate a message ID
    message_id = str(uuid.uuid4())
    
    # Save the AI response
    await session_manager.save_message(
        session_id=message.session_id,
        content=response["data"],
        role="assistant",
        message_id=message_id
    )
    
    return ChatResponse(
        content=response["data"],
        session_id=message.session_id,
        message_id=message_id
    )

@router.get("/history/{session_id}", response_model=HistoryResponse)
async def get_history(session_id: str):
    """
    Get the chat history for a specific session.
    
    Args:
        session_id: The session ID
        
    Returns:
        HistoryResponse: The chat history
    """
    messages = await session_manager.get_messages(session_id)
    
    if not messages:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return HistoryResponse(
        messages=messages,
        session_id=session_id
    )

@router.post("/upload_document")
async def upload_document(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None)
):
    """
    Upload a document for RAG processing.
    
    Args:
        file: The document file
        session_id: Optional session ID
        
    Returns:
        dict: Status and document ID
    """
    # Create a new session if none exists
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Process the document (this would be implemented in a RAG service)
    document_id = str(uuid.uuid4())
    
    # Return the document ID and session ID
    return {
        "status": "success",
        "document_id": document_id,
        "session_id": session_id,
        "filename": file.filename
    }
