"""
Security API endpoints for Attorney-General.AI.

This module provides API endpoints for user authentication and management.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field

from backend.security.security_system import SecuritySystem
from backend.security.middleware import authenticate_request, require_permission
from backend.data.database import get_db

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/security", tags=["security"])

# Request models
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = "user"

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr

# Response models
class LoginResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    user: Optional[Dict[str, Any]] = None
    token: Optional[str] = None

class RegisterResponse(BaseModel):
    success: bool
    message: Optional[str] = None

class ChangePasswordResponse(BaseModel):
    success: bool
    message: Optional[str] = None

class ResetPasswordResponse(BaseModel):
    success: bool
    message: Optional[str] = None

@router.post("/login", response_model=LoginResponse)
async def login(request: Request, login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate a user and return a JWT token.
    
    Args:
        request: FastAPI request
        login_data: Login data
        db: Database session
        
    Returns:
        LoginResponse: Login response
    """
    try:
        security_system = SecuritySystem(db)
        
        # Get client IP
        client_ip = request.client.host if request.client else "0.0.0.0"
        
        # Authenticate user
        success, user_data = security_system.authenticate_user(
            login_data.username,
            login_data.password,
            client_ip
        )
        
        if not success or not user_data:
            return LoginResponse(
                success=False,
                message="Invalid username or password"
            )
        
        return LoginResponse(
            success=True,
            message="Login successful",
            user={
                "id": user_data["id"],
                "username": user_data["username"],
                "email": user_data["email"],
                "role": user_data["role"]
            },
            token=user_data["token"]
        )
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return LoginResponse(
            success=False,
            message="An error occurred during login"
        )

@router.post("/register", response_model=RegisterResponse)
async def register(register_data: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    Args:
        register_data: Registration data
        db: Database session
        
    Returns:
        RegisterResponse: Registration response
    """
    try:
        security_system = SecuritySystem(db)
        
        # Register user
        success, error_message = security_system.register_user(
            register_data.username,
            register_data.email,
            register_data.password,
            register_data.role
        )
        
        if not success:
            return RegisterResponse(
                success=False,
                message=error_message or "Registration failed"
            )
        
        return RegisterResponse(
            success=True,
            message="Registration successful"
        )
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return RegisterResponse(
            success=False,
            message="An error occurred during registration"
        )

@router.post("/change-password", response_model=ChangePasswordResponse)
async def change_password(
    request: Request,
    change_data: ChangePasswordRequest,
    user_data: Dict[str, Any] = Depends(authenticate_request),
    db: Session = Depends(get_db)
):
    """
    Change a user's password.
    
    Args:
        request: FastAPI request
        change_data: Password change data
        user_data: Authenticated user data
        db: Database session
        
    Returns:
        ChangePasswordResponse: Password change response
    """
    try:
        security_system = SecuritySystem(db)
        
        # Get user from database
        user = db.query(User).filter(User.id == user_data["sub"]).first()
        
        if not user:
            return ChangePasswordResponse(
                success=False,
                message="User not found"
            )
        
        # Verify current password
        if not security_system._verify_password(
            change_data.current_password,
            user.password_hash,
            user.password_salt
        ):
            # Log failed password change attempt
            security_system._log_security_event(
                "password_change_failure",
                "Invalid current password",
                username=user.username,
                ip_address=request.client.host if request.client else "0.0.0.0",
                user_id=user.id
            )
            
            return ChangePasswordResponse(
                success=False,
                message="Current password is incorrect"
            )
        
        # Validate new password
        password_validation = security_system._validate_password(change_data.new_password)
        if not password_validation[0]:
            return ChangePasswordResponse(
                success=False,
                message=password_validation[1]
            )
        
        # Generate new password hash and salt
        salt = secrets.token_hex(16)
        password_hash = security_system._hash_password(change_data.new_password, salt)
        
        # Update user
        user.password_hash = password_hash
        user.password_salt = salt
        db.commit()
        
        # Log password change
        security_system._log_security_event(
            "password_changed",
            "Password changed successfully",
            username=user.username,
            ip_address=request.client.host if request.client else "0.0.0.0",
            user_id=user.id
        )
        
        return ChangePasswordResponse(
            success=True,
            message="Password changed successfully"
        )
    except Exception as e:
        logger.error(f"Password change error: {str(e)}")
        return ChangePasswordResponse(
            success=False,
            message="An error occurred while changing password"
        )

@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(reset_data: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Request a password reset.
    
    Args:
        reset_data: Password reset data
        db: Database session
        
    Returns:
        ResetPasswordResponse: Password reset response
    """
    try:
        security_system = SecuritySystem(db)
        
        # Get user from database
        user = db.query(User).filter(User.email == reset_data.email).first()
        
        if not user:
            # Don't reveal if email exists or not
            return ResetPasswordResponse(
                success=True,
                message="If your email is registered, you will receive a password reset link"
            )
        
        # In a real implementation, this would generate a reset token and send an email
        # For demonstration purposes, we'll just log the event
        
        security_system._log_security_event(
            "password_reset_requested",
            f"Password reset requested for user: {user.username}",
            username=user.username,
            user_id=user.id
        )
        
        return ResetPasswordResponse(
            success=True,
            message="If your email is registered, you will receive a password reset link"
        )
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        return ResetPasswordResponse(
            success=False,
            message="An error occurred while processing your request"
        )

@router.get("/user", dependencies=[Depends(authenticate_request)])
async def get_current_user(user_data: Dict[str, Any] = Depends(authenticate_request), db: Session = Depends(get_db)):
    """
    Get the current authenticated user.
    
    Args:
        user_data: Authenticated user data
        db: Database session
        
    Returns:
        Dict: User data
    """
    try:
        # Get user from database
        user = db.query(User).filter(User.id == user_data["sub"]).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred")

@router.get("/users", dependencies=[Depends(require_permission("users", "read"))])
async def get_users(db: Session = Depends(get_db)):
    """
    Get all users (admin only).
    
    Args:
        db: Database session
        
    Returns:
        List[Dict]: List of users
    """
    try:
        users = db.query(User).all()
        
        return [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None
            }
            for user in users
        ]
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred")
