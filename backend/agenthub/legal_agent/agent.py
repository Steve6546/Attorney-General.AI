"""
Attorney-General.AI - Legal Agent

This module implements the specialized Legal Agent for handling legal queries and tasks.
It inherits from the BaseAgent class and adds legal-specific functionality.
"""

import json
import logging
from typing import Dict, Any, List, Optional
import asyncio

from backend.agenthub.base_agent import BaseAgent
from backend.utils.prompt_loader import load_prompt

logger = logging.getLogger(__name__)

class LegalAgent(BaseAgent):
    """Agent specialized in legal assistance and information."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the legal agent.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self.agent_type = "legal_agent"
        self.capabilities = [
            "legal_research",
            "document_analysis",
            "legal_advice",
            "document_generation"
        ]
        
        # Load legal agent system prompt
        self.system_prompt = load_prompt("legal_agent_prompt")
        
        # Register tools (to be implemented)
        # self.register_tool("legal_research", LegalResearchTool())
        # self.register_tool("document_analysis", DocumentAnalysisTool())
        # self.register_tool("legislation_search", LegislationSearchTool())
        # self.register_tool("code_interpreter", CodeInterpreterTool())
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a legal request and return a response.
        
        Args:
            request: The request dictionary containing the query and session_id
            
        Returns:
            Dict[str, Any]: The response dictionary
        """
        query = request.get("query", "")
        session_id = request.get("session_id", "")
        
        if not query:
            return {
                "status": "error",
                "data": "No query provided"
            }
        
        try:
            # Check if we should use tools or direct response
            if self.tools:
                # Use tool-enabled response generation
                response = await self._process_with_tools(query, session_id)
            else:
                # Use direct response generation
                response = await self._process_direct(query, session_id)
            
            return {
                "status": "success",
                "data": response
            }
        except Exception as e:
            logger.error(f"Error processing legal request: {str(e)}")
            return {
                "status": "error",
                "data": f"I apologize, but I encountered an error while processing your request: {str(e)}"
            }
    
    async def _process_direct(self, query: str, session_id: str) -> str:
        """
        Process a query directly with the LLM without using tools.
        
        Args:
            query: The user query
            session_id: The session ID
            
        Returns:
            str: The generated response
        """
        # Format the prompt with the query
        formatted_system_prompt = self.system_prompt.format(
            capabilities=", ".join(self.capabilities)
        )
        
        # Generate response
        response = await self.generate_response(
            prompt=query,
            system_message=formatted_system_prompt
        )
        
        return response
    
    async def _process_with_tools(self, query: str, session_id: str) -> str:
        """
        Process a query using tools when appropriate.
        
        Args:
            query: The user query
            session_id: The session ID
            
        Returns:
            str: The final response after potential tool usage
        """
        # Format the prompt with the query and tool descriptions
        formatted_system_prompt = self.system_prompt.format(
            capabilities=", ".join(self.capabilities),
            tool_descriptions=json.dumps(self.get_tool_descriptions(), indent=2)
        )
        
        # Generate response with potential tool calls
        response = await self.generate_with_tools(
            prompt=query,
            system_message=formatted_system_prompt
        )
        
        # Check if the LLM wants to use tools
        if response.get("has_tool_calls", False):
            # Execute the tool calls
            tool_results = await self.handle_tool_calls(response.get("tool_calls", []))
            
            # Format tool results for the LLM
            tool_results_str = json.dumps(tool_results, indent=2)
            
            # Generate final response incorporating tool results
            final_prompt = f"""
            Based on the original query: "{query}"
            
            I executed the following tools:
            {tool_results_str}
            
            Please provide a final response to the user's query incorporating these tool results.
            """
            
            final_response = await self.generate_response(
                prompt=final_prompt,
                system_message=formatted_system_prompt
            )
            
            return final_response
        else:
            # Return the direct response if no tools were called
            return response.get("content", "I apologize, but I couldn't generate a proper response.")
