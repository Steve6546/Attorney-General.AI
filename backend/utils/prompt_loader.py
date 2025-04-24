"""
Attorney-General.AI - Prompt Loader

This module provides utilities for loading prompts from files.
It supports loading prompts from YAML, JSON, and text files.
"""

import logging
import os
import yaml
import json
from typing import Dict, Any, Optional

from backend.config.settings import settings

logger = logging.getLogger(__name__)

def load_prompt(prompt_name: str, prompt_dir: Optional[str] = None) -> str:
    """
    Load a prompt from a file.
    
    Args:
        prompt_name: Name of the prompt file
        prompt_dir: Optional directory to load from
        
    Returns:
        str: Loaded prompt
        
    Raises:
        FileNotFoundError: If prompt file not found
        ValueError: If prompt format not supported
    """
    # Determine prompt directory
    if prompt_dir is None:
        prompt_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")
    
    # Determine file path
    file_path = os.path.join(prompt_dir, prompt_name)
    
    # Check if file exists
    if not os.path.exists(file_path):
        # Try adding extensions
        for ext in [".yaml", ".yml", ".json", ".txt"]:
            ext_path = file_path + ext
            if os.path.exists(ext_path):
                file_path = ext_path
                break
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Prompt file not found: {prompt_name}")
    
    # Load based on file extension
    _, ext = os.path.splitext(file_path)
    
    try:
        if ext.lower() in [".yaml", ".yml"]:
            return load_yaml_prompt(file_path)
        elif ext.lower() == ".json":
            return load_json_prompt(file_path)
        elif ext.lower() == ".txt":
            return load_text_prompt(file_path)
        else:
            # Try to load as text
            return load_text_prompt(file_path)
    except Exception as e:
        logger.error(f"Error loading prompt {prompt_name}: {str(e)}")
        raise

def load_yaml_prompt(file_path: str) -> str:
    """
    Load a prompt from a YAML file.
    
    Args:
        file_path: Path to YAML file
        
    Returns:
        str: Loaded prompt
    """
    with open(file_path, "r") as f:
        data = yaml.safe_load(f)
    
    # Check if it's a simple string
    if isinstance(data, str):
        return data
    
    # Check if it has a 'prompt' key
    if isinstance(data, dict) and "prompt" in data:
        return data["prompt"]
    
    # Convert to string
    return yaml.dump(data)

def load_json_prompt(file_path: str) -> str:
    """
    Load a prompt from a JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        str: Loaded prompt
    """
    with open(file_path, "r") as f:
        data = json.load(f)
    
    # Check if it's a simple string
    if isinstance(data, str):
        return data
    
    # Check if it has a 'prompt' key
    if isinstance(data, dict) and "prompt" in data:
        return data["prompt"]
    
    # Convert to string
    return json.dumps(data, indent=2)

def load_text_prompt(file_path: str) -> str:
    """
    Load a prompt from a text file.
    
    Args:
        file_path: Path to text file
        
    Returns:
        str: Loaded prompt
    """
    with open(file_path, "r") as f:
        return f.read()
