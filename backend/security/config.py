"""
Security configuration for Attorney-General.AI.

This module provides security-related configuration settings.
"""

import os
import secrets
from typing import Optional, List

class SecurityConfig:
    """Security configuration settings."""
    
    # JWT settings
    JWT_SECRET: str = os.getenv("JWT_SECRET", secrets.token_hex(32))
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))
    
    # Password policy
    PASSWORD_MIN_LENGTH: int = 10
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    
    # Rate limiting
    RATE_LIMIT_ATTEMPTS: int = 5
    RATE_LIMIT_WINDOW: int = 300  # 5 minutes
    
    # IP restrictions
    IP_ALLOWLIST: Optional[str] = os.getenv("IP_ALLOWLIST", "")
    IP_BLOCKLIST: Optional[str] = os.getenv("IP_BLOCKLIST", "")
    
    # Account lockout
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_DURATION: int = 30  # minutes
    
    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "https://attorney-general.ai"
    ]
    CORS_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_HEADERS: List[str] = ["*"]
    
    # Content Security Policy
    CSP_DIRECTIVES: dict = {
        "default-src": ["'self'"],
        "script-src": ["'self'", "'unsafe-inline'"],
        "style-src": ["'self'", "'unsafe-inline'"],
        "img-src": ["'self'", "data:"],
        "font-src": ["'self'"],
        "connect-src": ["'self'", "https://api.openai.com"]
    }
    
    # Security headers
    SECURITY_HEADERS: dict = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Referrer-Policy": "strict-origin-when-cross-origin"
    }
    
    # Encryption settings
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", secrets.token_hex(16))
    
    # Session settings
    SESSION_COOKIE_NAME: str = "attorney_general_session"
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"
    
    # CSRF protection
    CSRF_ENABLED: bool = True
    CSRF_SECRET: str = os.getenv("CSRF_SECRET", secrets.token_hex(16))

# Create singleton instance
security_config = SecurityConfig()
