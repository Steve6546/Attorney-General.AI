"""
Security middleware for Attorney-General.AI.

This module provides middleware for handling authentication and authorization.
"""

import logging
import json
from typing import Dict, Any, Optional, Callable
from functools import wraps
from fastapi import Request, Response, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.security.security_system import SecuritySystem
from backend.data.database import get_db

# Configure logging
logger = logging.getLogger(__name__)

# Security token scheme
security_scheme = HTTPBearer()

class SecurityMiddleware:
    """Middleware for handling security concerns."""
    
    def __init__(self):
        """Initialize the security middleware."""
        logger.info("Security Middleware initialized")
    
    async def authenticate_request(
        self, 
        request: Request, 
        credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
        db: Session = Depends(get_db)
    ) -> Dict[str, Any]:
        """
        Authenticate a request using JWT token.
        
        Args:
            request: FastAPI request
            credentials: HTTP authorization credentials
            db: Database session
            
        Returns:
            Dict[str, Any]: User data
            
        Raises:
            HTTPException: If authentication fails
        """
        try:
            token = credentials.credentials
            security_system = SecuritySystem(db)
            
            # Verify token
            is_valid, payload = security_system.verify_jwt_token(token)
            
            if not is_valid or not payload:
                raise HTTPException(status_code=401, detail="Invalid authentication token")
            
            # Get client IP
            client_ip = self._get_client_ip(request)
            
            # Check IP access
            if not security_system._check_ip_access(client_ip):
                security_system._log_security_event(
                    "authentication_failure",
                    f"IP address blocked: {client_ip}",
                    username=payload.get("username"),
                    ip_address=client_ip,
                    user_id=payload.get("sub")
                )
                raise HTTPException(status_code=403, detail="Access denied from your IP address")
            
            # Log successful authentication
            security_system._log_security_event(
                "authentication_success",
                f"Token authentication successful",
                username=payload.get("username"),
                ip_address=client_ip,
                user_id=payload.get("sub")
            )
            
            return payload
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise HTTPException(status_code=401, detail="Authentication failed")
    
    def require_permission(self, resource: str, action: str) -> Callable:
        """
        Decorator to require permission for an endpoint.
        
        Args:
            resource: Resource name
            action: Action name
            
        Returns:
            Callable: Decorator function
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(
                request: Request, 
                user_data: Dict[str, Any] = Depends(self.authenticate_request),
                db: Session = Depends(get_db),
                *args, **kwargs
            ):
                security_system = SecuritySystem(db)
                
                # Check permission
                user_id = user_data.get("sub")
                if not security_system.check_permission(user_id, resource, action):
                    # Log permission denied
                    security_system._log_security_event(
                        "permission_denied",
                        f"Permission denied: {resource}:{action}",
                        username=user_data.get("username"),
                        ip_address=self._get_client_ip(request),
                        user_id=user_id
                    )
                    raise HTTPException(status_code=403, detail="Permission denied")
                
                # Log permission granted
                security_system.log_audit(
                    user_id=user_id,
                    action=action,
                    resource_type=resource,
                    resource_id=None,  # Will be filled by the endpoint if applicable
                    details=f"Access to {resource}:{action}"
                )
                
                return await func(request=request, user_data=user_data, db=db, *args, **kwargs)
            
            return wrapper
        
        return decorator
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address from request.
        
        Args:
            request: FastAPI request
            
        Returns:
            str: Client IP address
        """
        # Check for X-Forwarded-For header (when behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Get the first IP in the list (client IP)
            return forwarded_for.split(",")[0].strip()
        
        # Fallback to direct client IP
        return request.client.host if request.client else "0.0.0.0"

# Create singleton instance
security_middleware = SecurityMiddleware()

# Convenience imports
authenticate_request = security_middleware.authenticate_request
require_permission = security_middleware.require_permission
