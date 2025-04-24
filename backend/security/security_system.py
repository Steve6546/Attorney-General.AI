"""
Attorney-General.AI - Security System

This module implements the security system for the Attorney-General.AI backend.
It provides functionality for authentication, authorization, and request validation.
"""

import logging
from typing import Dict, Any, List, Optional, Callable
import jwt
import time
from datetime import datetime, timedelta
import hashlib
import secrets

from backend.config.settings import settings

logger = logging.getLogger(__name__)

class SecuritySystem:
    """Security system for authentication, authorization, and validation."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the security system.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.secret_key = settings.SECRET_KEY
        self.token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.allowed_origins = [settings.FRONTEND_URL]
    
    async def create_access_token(self, data: Dict[str, Any]) -> str:
        """
        Create an access token.
        
        Args:
            data: The data to encode in the token
            
        Returns:
            str: The encoded JWT token
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.token_expire_minutes)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm="HS256")
        return encoded_jwt
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify a JWT token.
        
        Args:
            token: The JWT token to verify
            
        Returns:
            Optional[Dict[str, Any]]: The decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except jwt.PyJWTError:
            return None
    
    async def hash_password(self, password: str) -> str:
        """
        Hash a password.
        
        Args:
            password: The password to hash
            
        Returns:
            str: The hashed password
        """
        salt = secrets.token_hex(16)
        pwdhash = hashlib.pbkdf2_hmac(
            'sha256', 
            password.encode('utf-8'), 
            salt.encode('utf-8'), 
            100000
        ).hex()
        
        return f"{salt}${pwdhash}"
    
    async def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against a hash.
        
        Args:
            plain_password: The plain text password
            hashed_password: The hashed password
            
        Returns:
            bool: True if the password matches, False otherwise
        """
        salt, stored_hash = hashed_password.split('$')
        pwdhash = hashlib.pbkdf2_hmac(
            'sha256', 
            plain_password.encode('utf-8'), 
            salt.encode('utf-8'), 
            100000
        ).hex()
        
        return pwdhash == stored_hash
    
    async def validate_request(self, request_data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a request against a schema.
        
        Args:
            request_data: The request data to validate
            schema: The schema to validate against
            
        Returns:
            Dict[str, Any]: Validation result with 'valid' and 'errors' keys
        """
        errors = []
        
        # Check required fields
        if "required" in schema:
            for field in schema["required"]:
                if field not in request_data:
                    errors.append(f"Missing required field: {field}")
        
        # Check field types
        if "properties" in schema:
            for field, field_schema in schema["properties"].items():
                if field in request_data:
                    field_type = field_schema.get("type")
                    
                    # Check type
                    if field_type == "string" and not isinstance(request_data[field], str):
                        errors.append(f"Field '{field}' must be a string")
                    elif field_type == "integer" and not isinstance(request_data[field], int):
                        errors.append(f"Field '{field}' must be an integer")
                    elif field_type == "number" and not isinstance(request_data[field], (int, float)):
                        errors.append(f"Field '{field}' must be a number")
                    elif field_type == "boolean" and not isinstance(request_data[field], bool):
                        errors.append(f"Field '{field}' must be a boolean")
                    elif field_type == "array" and not isinstance(request_data[field], list):
                        errors.append(f"Field '{field}' must be an array")
                    elif field_type == "object" and not isinstance(request_data[field], dict):
                        errors.append(f"Field '{field}' must be an object")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def is_origin_allowed(self, origin: str) -> bool:
        """
        Check if an origin is allowed for CORS.
        
        Args:
            origin: The origin to check
            
        Returns:
            bool: True if the origin is allowed, False otherwise
        """
        # Allow all origins in development mode
        if settings.LOG_LEVEL == "DEBUG":
            return True
        
        return origin in self.allowed_origins
