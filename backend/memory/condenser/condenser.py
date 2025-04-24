"""
Attorney-General.AI - Memory Condenser

This module implements the memory condenser for the Attorney-General.AI backend.
It provides functionality for condensing and summarizing memory items.
"""

import logging
from typing import Dict, Any, List, Optional
import asyncio
import json

from backend.core.llm_service import LLMService

logger = logging.getLogger(__name__)

class MemoryCondenser:
    """Memory condenser for summarizing and condensing memory."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the memory condenser.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.llm_service = LLMService()
    
    async def condense_conversation(self, messages: List[Dict[str, Any]]) -> str:
        """
        Condense a conversation into a summary.
        
        Args:
            messages: List of conversation messages
            
        Returns:
            str: The condensed summary
        """
        if not messages:
            return ""
        
        # Format messages for the LLM
        formatted_messages = "\n".join([
            f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
            for msg in messages
        ])
        
        # Create prompt for condensing
        prompt = f"""
        Below is a conversation between a user and a legal assistant.
        Please summarize the key points of this conversation, focusing on:
        1. The main legal questions or issues raised
        2. Any important facts or context provided
        3. The advice or information given
        4. Any unresolved questions or next steps

        Conversation:
        {formatted_messages}

        Summary:
        """
        
        # Generate summary using LLM
        try:
            summary = await self.llm_service.generate_response(
                prompt=prompt,
                max_tokens=500,
                temperature=0.3
            )
            
            return summary
        except Exception as e:
            logger.error(f"Error condensing conversation: {str(e)}")
            return "Error generating conversation summary."
    
    async def extract_key_information(self, text: str, info_type: str) -> Dict[str, Any]:
        """
        Extract key information from text.
        
        Args:
            text: The text to extract information from
            info_type: The type of information to extract (e.g., 'legal_entities', 'dates', 'legal_concepts')
            
        Returns:
            Dict[str, Any]: The extracted information
        """
        # Create prompt based on information type
        if info_type == "legal_entities":
            prompt = f"""
            Please extract all legal entities (people, organizations, locations) from the following text.
            Return the results as a JSON object with keys for 'people', 'organizations', and 'locations'.

            Text:
            {text}

            JSON:
            """
        elif info_type == "dates":
            prompt = f"""
            Please extract all dates, deadlines, and time periods mentioned in the following text.
            Return the results as a JSON object with keys for 'dates', 'deadlines', and 'time_periods'.

            Text:
            {text}

            JSON:
            """
        elif info_type == "legal_concepts":
            prompt = f"""
            Please extract all legal concepts, principles, and terminology from the following text.
            Return the results as a JSON object with keys for 'concepts', 'principles', and 'terminology'.

            Text:
            {text}

            JSON:
            """
        else:
            prompt = f"""
            Please extract key information from the following text.
            Return the results as a JSON object with appropriate keys.

            Text:
            {text}

            JSON:
            """
        
        # Generate extraction using LLM
        try:
            extraction_result = await self.llm_service.generate_response(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.2
            )
            
            # Parse JSON result
            try:
                # Find JSON in the response
                json_start = extraction_result.find('{')
                json_end = extraction_result.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = extraction_result[json_start:json_end]
                    return json.loads(json_str)
                else:
                    return {"error": "No valid JSON found in extraction result"}
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON from extraction result")
                return {"error": "Failed to parse extraction result as JSON"}
                
        except Exception as e:
            logger.error(f"Error extracting information: {str(e)}")
            return {"error": f"Error extracting information: {str(e)}"}
