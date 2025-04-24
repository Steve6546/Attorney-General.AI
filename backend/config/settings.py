"""
Attorney-General.AI - Settings Module

This module contains the settings for the Attorney-General.AI backend.
It uses Pydantic's BaseSettings for environment variable validation and loading.
"""

import os
from typing import Dict, Any, Optional, List
from pydantic import BaseSettings, Field, validator
from pathlib import Path

class Settings(BaseSettings):
    """Settings for the Attorney-General.AI backend."""
    
    # Application settings
    APP_NAME: str = "Attorney-General.AI"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = Field(False, env="DEBUG")
    ENVIRONMENT: str = Field("production", env="ENVIRONMENT")
    
    # API settings
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["*"]
    
    # Security settings
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"
    
    # Database settings
    DATABASE_URL: str = Field("sqlite:///./attorney_general.db", env="DATABASE_URL")
    
    # LLM settings
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    OPENAI_API_BASE: str = Field("https://api.openai.com/v1", env="OPENAI_API_BASE")
    LLM_MODEL: str = Field("gpt-4", env="LLM_MODEL")
    EMBEDDING_MODEL: str = Field("text-embedding-ada-002", env="EMBEDDING_MODEL")
    
    # Storage settings
    STORAGE_PATH: Path = Field(Path("./storage"), env="STORAGE_PATH")
    VECTOR_DB_PATH: Path = Field(Path("./storage/vector_db"), env="VECTOR_DB_PATH")
    UPLOADS_PATH: Path = Field(Path("./storage/uploads"), env="UPLOADS_PATH")
    
    # Logging settings
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    
    @validator("STORAGE_PATH", "VECTOR_DB_PATH", "UPLOADS_PATH", pre=True)
    def create_directories(cls, v):
        """Create directories if they don't exist."""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create settings instance
settings = Settings(
    # Default values for required fields when not in environment
    SECRET_KEY=os.environ.get("SECRET_KEY", "supersecretkey"),
    OPENAI_API_KEY=os.environ.get("OPENAI_API_KEY", "sk-yourapikey")
)
