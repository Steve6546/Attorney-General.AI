"""
Attorney-General.AI - Storage System

This module implements the storage system for the Attorney-General.AI backend.
It provides functionality for storing and retrieving data from different storage backends.
"""

import logging
from typing import Dict, Any, List, Optional, BinaryIO
import os
import json
import sqlite3
from pathlib import Path
import aiofiles

logger = logging.getLogger(__name__)

class StorageSystem:
    """Storage system for managing data storage and retrieval."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the storage system.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.base_path = self.config.get("base_path", "./storage")
        
        # Create base directory if it doesn't exist
        os.makedirs(self.base_path, exist_ok=True)
    
    async def save_file(self, file_path: str, content: bytes) -> bool:
        """
        Save binary content to a file.
        
        Args:
            file_path: The path to save the file to (relative to base_path)
            content: The binary content to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create full path
            full_path = os.path.join(self.base_path, file_path)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Write file
            async with aiofiles.open(full_path, "wb") as f:
                await f.write(content)
            
            return True
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            return False
    
    async def save_text(self, file_path: str, content: str) -> bool:
        """
        Save text content to a file.
        
        Args:
            file_path: The path to save the file to (relative to base_path)
            content: The text content to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create full path
            full_path = os.path.join(self.base_path, file_path)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Write file
            async with aiofiles.open(full_path, "w", encoding="utf-8") as f:
                await f.write(content)
            
            return True
        except Exception as e:
            logger.error(f"Error saving text file: {str(e)}")
            return False
    
    async def save_json(self, file_path: str, data: Dict[str, Any]) -> bool:
        """
        Save JSON data to a file.
        
        Args:
            file_path: The path to save the file to (relative to base_path)
            data: The data to save as JSON
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert data to JSON string
            json_content = json.dumps(data, indent=2)
            
            # Save as text
            return await self.save_text(file_path, json_content)
        except Exception as e:
            logger.error(f"Error saving JSON file: {str(e)}")
            return False
    
    async def load_file(self, file_path: str) -> Optional[bytes]:
        """
        Load binary content from a file.
        
        Args:
            file_path: The path to load the file from (relative to base_path)
            
        Returns:
            Optional[bytes]: The file content or None if not found
        """
        try:
            # Create full path
            full_path = os.path.join(self.base_path, file_path)
            
            # Check if file exists
            if not os.path.exists(full_path):
                return None
            
            # Read file
            async with aiofiles.open(full_path, "rb") as f:
                content = await f.read()
            
            return content
        except Exception as e:
            logger.error(f"Error loading file: {str(e)}")
            return None
    
    async def load_text(self, file_path: str) -> Optional[str]:
        """
        Load text content from a file.
        
        Args:
            file_path: The path to load the file from (relative to base_path)
            
        Returns:
            Optional[str]: The file content or None if not found
        """
        try:
            # Create full path
            full_path = os.path.join(self.base_path, file_path)
            
            # Check if file exists
            if not os.path.exists(full_path):
                return None
            
            # Read file
            async with aiofiles.open(full_path, "r", encoding="utf-8") as f:
                content = await f.read()
            
            return content
        except Exception as e:
            logger.error(f"Error loading text file: {str(e)}")
            return None
    
    async def load_json(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Load JSON data from a file.
        
        Args:
            file_path: The path to load the file from (relative to base_path)
            
        Returns:
            Optional[Dict[str, Any]]: The parsed JSON data or None if not found
        """
        try:
            # Load text content
            content = await self.load_text(file_path)
            
            if content is None:
                return None
            
            # Parse JSON
            return json.loads(content)
        except Exception as e:
            logger.error(f"Error loading JSON file: {str(e)}")
            return None
    
    async def list_files(self, directory: str) -> List[str]:
        """
        List files in a directory.
        
        Args:
            directory: The directory to list files from (relative to base_path)
            
        Returns:
            List[str]: List of file paths
        """
        try:
            # Create full path
            full_path = os.path.join(self.base_path, directory)
            
            # Check if directory exists
            if not os.path.exists(full_path) or not os.path.isdir(full_path):
                return []
            
            # List files
            files = []
            for root, _, filenames in os.walk(full_path):
                for filename in filenames:
                    # Get relative path
                    file_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(file_path, self.base_path)
                    files.append(rel_path)
            
            return files
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            return []
    
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file.
        
        Args:
            file_path: The path of the file to delete (relative to base_path)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create full path
            full_path = os.path.join(self.base_path, file_path)
            
            # Check if file exists
            if not os.path.exists(full_path):
                return False
            
            # Delete file
            os.remove(full_path)
            
            return True
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return False
