"""
Database migrations for Attorney-General.AI.

This module provides database migration functionality using Alembic.
"""

import logging
import os
from alembic.config import Config
from alembic import command
from pathlib import Path

from backend.config.settings import settings

# Configure logging
logger = logging.getLogger(__name__)

def run_migrations():
    """
    Run database migrations using Alembic.
    """
    try:
        # Get the directory of this file
        base_dir = Path(__file__).resolve().parent.parent.parent
        
        # Set up Alembic configuration
        alembic_cfg = Config(os.path.join(base_dir, "alembic.ini"))
        alembic_cfg.set_main_option("script_location", os.path.join(base_dir, "migrations"))
        alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
        
        # Run migrations
        command.upgrade(alembic_cfg, "head")
        
        logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.error(f"Error running database migrations: {str(e)}")
        raise

def create_migration(message):
    """
    Create a new migration.
    
    Args:
        message: Migration message
    """
    try:
        # Get the directory of this file
        base_dir = Path(__file__).resolve().parent.parent.parent
        
        # Set up Alembic configuration
        alembic_cfg = Config(os.path.join(base_dir, "alembic.ini"))
        alembic_cfg.set_main_option("script_location", os.path.join(base_dir, "migrations"))
        alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
        
        # Create migration
        command.revision(alembic_cfg, autogenerate=True, message=message)
        
        logger.info(f"Created migration: {message}")
    except Exception as e:
        logger.error(f"Error creating migration: {str(e)}")
        raise

def downgrade_database(revision):
    """
    Downgrade the database to a specific revision.
    
    Args:
        revision: Target revision
    """
    try:
        # Get the directory of this file
        base_dir = Path(__file__).resolve().parent.parent.parent
        
        # Set up Alembic configuration
        alembic_cfg = Config(os.path.join(base_dir, "alembic.ini"))
        alembic_cfg.set_main_option("script_location", os.path.join(base_dir, "migrations"))
        alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
        
        # Downgrade database
        command.downgrade(alembic_cfg, revision)
        
        logger.info(f"Downgraded database to revision: {revision}")
    except Exception as e:
        logger.error(f"Error downgrading database: {str(e)}")
        raise

def initialize_migrations():
    """
    Initialize the migrations directory structure.
    """
    try:
        # Get the directory of this file
        base_dir = Path(__file__).resolve().parent.parent.parent
        
        # Set up Alembic configuration
        alembic_cfg = Config()
        alembic_cfg.set_main_option("script_location", os.path.join(base_dir, "migrations"))
        alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
        
        # Initialize migrations
        command.init(alembic_cfg, os.path.join(base_dir, "migrations"))
        
        logger.info("Migrations initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing migrations: {str(e)}")
        raise
