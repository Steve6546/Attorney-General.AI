"""
Attorney-General.AI - Main Application Entry Point

This is the main entry point for the Attorney-General.AI backend application.
It initializes the FastAPI application and includes all necessary routes.
"""

import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from backend.config.settings import Settings
from backend.api.v1.endpoints import router as api_router
from backend.core.llm_service import LLMService
from backend.core.session_manager import SessionManager

# Initialize settings
settings = Settings()

# Create FastAPI app
app = FastAPI(
    title="Attorney-General.AI API",
    description="API for Attorney-General.AI, an advanced legal AI assistant",
    version="2.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, this should be restricted to the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint to verify the API is running."""
    return {"status": "healthy"}

# Run the application
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
