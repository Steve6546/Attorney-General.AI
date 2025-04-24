"""
Attorney-General.AI - Session Manager

This module provides a service for managing user sessions and chat history.
It handles storing and retrieving messages for conversations.
"""

import uuid
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import os
import sqlite3
from pathlib import Path

from backend.config.settings import settings

logger = logging.getLogger(__name__)

class SessionManager:
    """Service for managing user sessions and chat history."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the session manager.
        
        Args:
            db_path: Optional path to the SQLite database file
        """
        self.db_path = db_path or settings.DATABASE_URL.replace("sqlite:///", "")
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize the SQLite database with required tables."""
        # Create the directory if it doesn't exist
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        # Connect to the database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create sessions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create messages table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            content TEXT,
            role TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (id)
        )
        ''')
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
    
    async def create_session(self, user_id: Optional[str] = None) -> str:
        """
        Create a new session.
        
        Args:
            user_id: Optional user ID
            
        Returns:
            str: The session ID
        """
        session_id = str(uuid.uuid4())
        
        # Connect to the database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Insert new session
        cursor.execute(
            "INSERT INTO sessions (id, user_id) VALUES (?, ?)",
            (session_id, user_id)
        )
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a session by ID.
        
        Args:
            session_id: The session ID
            
        Returns:
            Optional[Dict[str, Any]]: The session data or None if not found
        """
        # Connect to the database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Query the session
        cursor.execute(
            "SELECT id, user_id, created_at, updated_at FROM sessions WHERE id = ?",
            (session_id,)
        )
        
        # Fetch the result
        result = cursor.fetchone()
        
        # Close connection
        conn.close()
        
        # Return None if session not found
        if not result:
            return None
        
        # Return session data
        return {
            "id": result[0],
            "user_id": result[1],
            "created_at": result[2],
            "updated_at": result[3]
        }
    
    async def save_message(
        self,
        session_id: str,
        content: str,
        role: str,
        message_id: Optional[str] = None
    ) -> str:
        """
        Save a message to a session.
        
        Args:
            session_id: The session ID
            content: The message content
            role: The message role (user/assistant/system)
            message_id: Optional message ID
            
        Returns:
            str: The message ID
        """
        # Generate message ID if not provided
        if not message_id:
            message_id = str(uuid.uuid4())
        
        # Connect to the database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if session exists
        cursor.execute("SELECT id FROM sessions WHERE id = ?", (session_id,))
        session = cursor.fetchone()
        
        # Create session if it doesn't exist
        if not session:
            cursor.execute(
                "INSERT INTO sessions (id) VALUES (?)",
                (session_id,)
            )
        
        # Insert message
        cursor.execute(
            "INSERT INTO messages (id, session_id, content, role) VALUES (?, ?, ?, ?)",
            (message_id, session_id, content, role)
        )
        
        # Update session updated_at timestamp
        cursor.execute(
            "UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (session_id,)
        )
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        return message_id
    
    async def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all messages for a session.
        
        Args:
            session_id: The session ID
            
        Returns:
            List[Dict[str, Any]]: The messages
        """
        # Connect to the database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Query messages
        cursor.execute(
            "SELECT id, content, role, created_at FROM messages WHERE session_id = ? ORDER BY created_at",
            (session_id,)
        )
        
        # Fetch results
        results = cursor.fetchall()
        
        # Close connection
        conn.close()
        
        # Return messages
        return [
            {
                "id": row[0],
                "content": row[1],
                "role": row[2],
                "created_at": row[3]
            }
            for row in results
        ]
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and all its messages.
        
        Args:
            session_id: The session ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Delete messages
            cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            
            # Delete session
            cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            
            # Commit changes and close connection
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            logger.error(f"Error deleting session: {str(e)}")
            return False
