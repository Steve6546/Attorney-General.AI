"""
Attorney-General.AI - Prompt Loader Utility

This module provides utilities for loading and formatting prompts from files.
"""

import os
import yaml
import json
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

def load_prompt(prompt_name: str, prompt_dir: Optional[str] = None) -> str:
    """
    Load a prompt from a file.
    
    Args:
        prompt_name: The name of the prompt to load (without extension)
        prompt_dir: Optional directory path where prompts are stored
        
    Returns:
        str: The loaded prompt text
    """
    # Default prompt directory if not specified
    if prompt_dir is None:
        prompt_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")
    
    # Try different file extensions
    extensions = [".yaml", ".yml", ".json", ".txt"]
    
    for ext in extensions:
        file_path = os.path.join(prompt_dir, f"{prompt_name}{ext}")
        
        if os.path.exists(file_path):
            try:
                # Load based on file extension
                if ext in [".yaml", ".yml"]:
                    with open(file_path, "r", encoding="utf-8") as f:
                        prompt_data = yaml.safe_load(f)
                        
                    # Extract prompt text from YAML structure
                    if isinstance(prompt_data, dict):
                        return prompt_data.get("prompt", "")
                    else:
                        return str(prompt_data)
                        
                elif ext == ".json":
                    with open(file_path, "r", encoding="utf-8") as f:
                        prompt_data = json.load(f)
                        
                    # Extract prompt text from JSON structure
                    if isinstance(prompt_data, dict):
                        return prompt_data.get("prompt", "")
                    else:
                        return str(prompt_data)
                        
                else:  # .txt or other
                    with open(file_path, "r", encoding="utf-8") as f:
                        return f.read()
                        
            except Exception as e:
                logger.error(f"Error loading prompt '{prompt_name}': {str(e)}")
                return f"Error loading prompt: {str(e)}"
    
    # If prompt file not found, return a default message
    logger.warning(f"Prompt '{prompt_name}' not found in {prompt_dir}")
    return f"[Prompt '{prompt_name}' not found]"

def format_prompt(prompt_template: str, **kwargs) -> str:
    """
    Format a prompt template with the provided variables.
    
    Args:
        prompt_template: The prompt template with placeholders
        **kwargs: Variables to insert into the template
        
    Returns:
        str: The formatted prompt
    """
    try:
        return prompt_template.format(**kwargs)
    except KeyError as e:
        logger.error(f"Missing key in prompt formatting: {str(e)}")
        return f"Error formatting prompt: Missing key {str(e)}"
    except Exception as e:
        logger.error(f"Error formatting prompt: {str(e)}")
        return f"Error formatting prompt: {str(e)}"
