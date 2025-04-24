"""
Security System for Attorney-General.AI.

This module provides comprehensive security features including authentication, authorization,
encryption, and audit logging.
"""

import logging
import os
import json
import hashlib
import secrets
import time
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
import re
import ipaddress
from sqlalchemy.orm import Session

from backend.config.settings import settings
from backend.data.models import User, AuditLog, SecurityEvent

# Configure logging
logger = logging.getLogger(__name__)

class SecuritySystem:
    """Comprehensive security system for the application."""
    
    def __init__(self, db: Session):
        """
        Initialize the security system.
        
        Args:
            db: Database session
        """
        self.db = db
        self.jwt_secret = settings.JWT_SECRET or secrets.token_hex(32)
        self.jwt_algorithm = "HS256"
        self.jwt_expiration = settings.JWT_EXPIRATION_MINUTES or 60
        
        # Password policy
        self.password_min_length = 10
        self.password_require_uppercase = True
        self.password_require_lowercase = True
        self.password_require_digit = True
        self.password_require_special = True
        
        # Rate limiting
        self.rate_limit_attempts = 5
        self.rate_limit_window = 300  # 5 minutes
        self.rate_limit_cache = {}  # IP -> [timestamps]
        
        # IP allowlist/blocklist
        self.ip_allowlist = self._parse_ip_list(settings.IP_ALLOWLIST or "")
        self.ip_blocklist = self._parse_ip_list(settings.IP_BLOCKLIST or "")
        
        logger.info("Security System initialized")
    
    def authenticate_user(self, username: str, password: str, ip_address: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Authenticate a user.
        
        Args:
            username: Username
            password: Password
            ip_address: Client IP address
            
        Returns:
            Tuple[bool, Optional[Dict[str, Any]]]: (success, user_data)
        """
        try:
            # Check IP restrictions
            if not self._check_ip_access(ip_address):
                self._log_security_event(
                    "authentication_failure",
                    f"IP address blocked: {ip_address}",
                    username=username,
                    ip_address=ip_address
                )
                return False, None
            
            # Check rate limiting
            if self._is_rate_limited(ip_address):
                self._log_security_event(
                    "authentication_failure",
                    f"Rate limited: {ip_address}",
                    username=username,
                    ip_address=ip_address
                )
                return False, None
            
            # Get user from database
            user = self.db.query(User).filter(User.username == username).first()
            
            if not user:
                self._log_security_event(
                    "authentication_failure",
                    f"User not found: {username}",
                    username=username,
                    ip_address=ip_address
                )
                self._update_rate_limit(ip_address)
                return False, None
            
            # Check if account is locked
            if user.is_locked:
                self._log_security_event(
                    "authentication_failure",
                    f"Account locked: {username}",
                    username=username,
                    ip_address=ip_address,
                    user_id=user.id
                )
                return False, None
            
            # Verify password
            if not self._verify_password(password, user.password_hash, user.password_salt):
                # Increment failed attempts
                user.failed_login_attempts += 1
                
                # Lock account if too many failed attempts
                if user.failed_login_attempts >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
                    user.is_locked = True
                    self._log_security_event(
                        "account_locked",
                        f"Account locked after {user.failed_login_attempts} failed attempts",
                        username=username,
                        ip_address=ip_address,
                        user_id=user.id
                    )
                
                self.db.commit()
                
                self._log_security_event(
                    "authentication_failure",
                    f"Invalid password for user: {username}",
                    username=username,
                    ip_address=ip_address,
                    user_id=user.id
                )
                
                self._update_rate_limit(ip_address)
                return False, None
            
            # Authentication successful
            
            # Reset failed attempts
            user.failed_login_attempts = 0
            user.last_login_at = datetime.utcnow()
            user.last_login_ip = ip_address
            self.db.commit()
            
            # Generate token
            token = self.generate_jwt_token(user)
            
            self._log_security_event(
                "authentication_success",
                f"User authenticated: {username}",
                username=username,
                ip_address=ip_address,
                user_id=user.id
            )
            
            # Return user data
            return True, {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "token": token
            }
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            self._log_security_event(
                "authentication_error",
                f"Error during authentication: {str(e)}",
                username=username,
                ip_address=ip_address
            )
            return False, None
    
    def register_user(self, username: str, email: str, password: str, role: str = "user") -> Tuple[bool, Optional[str]]:
        """
        Register a new user.
        
        Args:
            username: Username
            email: Email address
            password: Password
            role: User role
            
        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        try:
            # Check if username already exists
            existing_user = self.db.query(User).filter(User.username == username).first()
            if existing_user:
                return False, "Username already exists"
            
            # Check if email already exists
            existing_email = self.db.query(User).filter(User.email == email).first()
            if existing_email:
                return False, "Email already exists"
            
            # Validate password
            password_validation = self._validate_password(password)
            if not password_validation[0]:
                return False, password_validation[1]
            
            # Generate password hash and salt
            salt = secrets.token_hex(16)
            password_hash = self._hash_password(password, salt)
            
            # Create user
            new_user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                password_salt=salt,
                role=role,
                created_at=datetime.utcnow()
            )
            
            self.db.add(new_user)
            self.db.commit()
            
            self._log_security_event(
                "user_registered",
                f"New user registered: {username}",
                username=username,
                user_id=new_user.id
            )
            
            return True, None
        except Exception as e:
            logger.error(f"User registration error: {str(e)}")
            self.db.rollback()
            return False, f"Registration error: {str(e)}"
    
    def generate_jwt_token(self, user: User) -> str:
        """
        Generate a JWT token for a user.
        
        Args:
            user: User object
            
        Returns:
            str: JWT token
        """
        expiration = datetime.utcnow() + timedelta(minutes=self.jwt_expiration)
        
        payload = {
            "sub": user.id,
            "username": user.username,
            "role": user.role,
            "exp": expiration.timestamp()
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        
        return token
    
    def verify_jwt_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Verify a JWT token.
        
        Args:
            token: JWT token
            
        Returns:
            Tuple[bool, Optional[Dict[str, Any]]]: (is_valid, payload)
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            # Check if token is expired
            if "exp" in payload and datetime.utcnow().timestamp() > payload["exp"]:
                return False, None
            
            return True, payload
        except jwt.PyJWTError as e:
            logger.warning(f"JWT verification failed: {str(e)}")
            return False, None
    
    def check_permission(self, user_id: str, resource: str, action: str) -> bool:
        """
        Check if a user has permission to perform an action on a resource.
        
        Args:
            user_id: User ID
            resource: Resource name
            action: Action name
            
        Returns:
            bool: True if user has permission, False otherwise
        """
        try:
            # Get user
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            # Admin has all permissions
            if user.role == "admin":
                return True
            
            # Check role-based permissions
            if user.role == "legal_professional" and resource in ["documents", "cases", "research"]:
                return True
            
            if user.role == "user" and resource in ["documents", "research"]:
                if action in ["read", "create"]:
                    return True
            
            # Default deny
            return False
        except Exception as e:
            logger.error(f"Permission check error: {str(e)}")
            return False
    
    def _hash_password(self, password: str, salt: str) -> str:
        """
        Hash a password with a salt.
        
        Args:
            password: Password
            salt: Salt
            
        Returns:
            str: Hashed password
        """
        # Use PBKDF2 with SHA-256
        key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100000  # 100,000 iterations
        ).hex()
        
        return key
    
    def _verify_password(self, password: str, stored_hash: str, salt: str) -> bool:
        """
        Verify a password against a stored hash.
        
        Args:
            password: Password to verify
            stored_hash: Stored password hash
            salt: Salt
            
        Returns:
            bool: True if password is correct, False otherwise
        """
        calculated_hash = self._hash_password(password, salt)
        return secrets.compare_digest(calculated_hash, stored_hash)
    
    def _validate_password(self, password: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a password against the password policy.
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Check length
        if len(password) < self.password_min_length:
            return False, f"Password must be at least {self.password_min_length} characters long"
        
        # Check for uppercase letter
        if self.password_require_uppercase and not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        
        # Check for lowercase letter
        if self.password_require_lowercase and not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        
        # Check for digit
        if self.password_require_digit and not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit"
        
        # Check for special character
        if self.password_require_special and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False, "Password must contain at least one special character"
        
        return True, None
    
    def _is_rate_limited(self, ip_address: str) -> bool:
        """
        Check if an IP address is rate limited.
        
        Args:
            ip_address: IP address
            
        Returns:
            bool: True if rate limited, False otherwise
        """
        if ip_address not in self.rate_limit_cache:
            return False
        
        # Get timestamps within the window
        current_time = time.time()
        window_start = current_time - self.rate_limit_window
        
        recent_attempts = [t for t in self.rate_limit_cache[ip_address] if t > window_start]
        self.rate_limit_cache[ip_address] = recent_attempts
        
        return len(recent_attempts) >= self.rate_limit_attempts
    
    def _update_rate_limit(self, ip_address: str) -> None:
        """
        Update rate limit for an IP address.
        
        Args:
            ip_address: IP address
        """
        current_time = time.time()
        
        if ip_address not in self.rate_limit_cache:
            self.rate_limit_cache[ip_address] = []
        
        self.rate_limit_cache[ip_address].append(current_time)
    
    def _parse_ip_list(self, ip_list_str: str) -> List[Any]:
        """
        Parse a comma-separated list of IP addresses or CIDR ranges.
        
        Args:
            ip_list_str: Comma-separated list of IPs or CIDR ranges
            
        Returns:
            List[Any]: List of IP address objects
        """
        if not ip_list_str:
            return []
        
        ip_objects = []
        
        for ip_str in ip_list_str.split(","):
            ip_str = ip_str.strip()
            if not ip_str:
                continue
            
            try:
                # Check if it's a CIDR range
                if "/" in ip_str:
                    ip_objects.append(ipaddress.ip_network(ip_str, strict=False))
                else:
                    ip_objects.append(ipaddress.ip_address(ip_str))
            except ValueError:
                logger.warning(f"Invalid IP address or CIDR range: {ip_str}")
        
        return ip_objects
    
    def _check_ip_access(self, ip_address: str) -> bool:
        """
        Check if an IP address is allowed to access the system.
        
        Args:
            ip_address: IP address
            
        Returns:
            bool: True if allowed, False if blocked
        """
        try:
            ip = ipaddress.ip_address(ip_address)
            
            # Check blocklist first
            for blocked_ip in self.ip_blocklist:
                if isinstance(blocked_ip, ipaddress.IPv4Network) or isinstance(blocked_ip, ipaddress.IPv6Network):
                    if ip in blocked_ip:
                        return False
                elif ip == blocked_ip:
                    return False
            
            # If allowlist is empty, allow all non-blocked IPs
            if not self.ip_allowlist:
                return True
            
            # If allowlist is not empty, only allow IPs in the allowlist
            for allowed_ip in self.ip_allowlist:
                if isinstance(allowed_ip, ipaddress.IPv4Network) or isinstance(allowed_ip, ipaddress.IPv6Network):
                    if ip in allowed_ip:
                        return True
                elif ip == allowed_ip:
                    return True
            
            # IP is not in allowlist
            return False
        except ValueError:
            logger.warning(f"Invalid IP address: {ip_address}")
            return False
    
    def _log_security_event(self, event_type: str, description: str, **metadata) -> None:
        """
        Log a security event.
        
        Args:
            event_type: Type of event
            description: Event description
            **metadata: Additional metadata
        """
        try:
            # Create security event
            event = SecurityEvent(
                event_type=event_type,
                description=description,
                metadata=json.dumps(metadata),
                created_at=datetime.utcnow()
            )
            
            self.db.add(event)
            self.db.commit()
        except Exception as e:
            logger.error(f"Error logging security event: {str(e)}")
            self.db.rollback()
    
    def log_audit(self, user_id: Optional[str], action: str, resource_type: str, resource_id: Optional[str], details: str) -> None:
        """
        Log an audit event.
        
        Args:
            user_id: User ID (optional)
            action: Action performed
            resource_type: Type of resource
            resource_id: Resource ID (optional)
            details: Additional details
        """
        try:
            # Create audit log
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                created_at=datetime.utcnow()
            )
            
            self.db.add(audit_log)
            self.db.commit()
        except Exception as e:
            logger.error(f"Error logging audit event: {str(e)}")
            self.db.rollback()
    
    def encrypt_data(self, data: str) -> str:
        """
        Encrypt sensitive data.
        
        Args:
            data: Data to encrypt
            
        Returns:
            str: Encrypted data
        """
        # In a real implementation, this would use a proper encryption library
        # For demonstration purposes, we'll use a simple base64 encoding
        import base64
        return base64.b64encode(data.encode("utf-8")).decode("utf-8")
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data.
        
        Args:
            encrypted_data: Encrypted data
            
        Returns:
            str: Decrypted data
        """
        # In a real implementation, this would use a proper encryption library
        # For demonstration purposes, we'll use a simple base64 decoding
        import base64
        return base64.b64decode(encrypted_data.encode("utf-8")).decode("utf-8")
