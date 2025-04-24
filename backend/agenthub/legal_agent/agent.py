"""
Attorney-General.AI - Legal Agent

This module implements the specialized legal agent for the Attorney-General.AI backend.
It extends the base agent with legal-specific functionality.
"""

import logging
from typing import Dict, Any, List, Optional, Union
import json
from datetime import datetime

from backend.agenthub.base_agent import BaseAgent
from backend.core.llm_service import LLMService
from backend.memory.memory_store import MemoryStore
from backend.tools.base_tool import BaseTool
from backend.utils.prompt_loader import load_prompt

logger = logging.getLogger(__name__)

class LegalAgent(BaseAgent):
    """Legal agent specialized for legal assistance."""
    
    def __init__(
        self,
        session_id: str,
        llm_service: Optional[LLMService] = None,
        memory_store: Optional[MemoryStore] = None,
        tools: Optional[List[BaseTool]] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the legal agent.
        
        Args:
            session_id: Session ID for the agent
            llm_service: Optional LLM service
            memory_store: Optional memory store
            tools: Optional list of tools
            config: Optional configuration
        """
        # Load legal agent system prompt
        system_prompt = load_prompt("legal_agent_prompt.yaml")
        
        super().__init__(
            session_id=session_id,
            llm_service=llm_service,
            memory_store=memory_store,
            tools=tools,
            system_prompt=system_prompt,
            config=config
        )
        
        # Legal agent specific state
        self.legal_context = {}
        self.jurisdiction = config.get("jurisdiction") if config else None
        self.legal_specialization = config.get("specialization") if config else "general"
    
    async def _generate_response(self, message: str) -> str:
        """
        Generate a response to a user message with legal context.
        
        Args:
            message: User message
            
        Returns:
            str: Generated response
        """
        # Get relevant memories
        relevant_memories = await self.get_relevant_memories(message)
        memory_text = ""
        
        if relevant_memories:
            memory_text = "Relevant context from previous conversation:\n"
            for memory in relevant_memories:
                memory_text += f"- {memory['content']}\n"
            memory_text += "\n"
        
        # Get legal context if available
        legal_context = ""
        if self.legal_context:
            legal_context = "Legal context:\n"
            for key, value in self.legal_context.items():
                legal_context += f"- {key}: {value}\n"
            legal_context += "\n"
        
        # Build prompt with legal focus
        prompt = f"""
        {memory_text}
        {legal_context}
        
        User query: {message}
        
        Provide a legally sound response based on the query and available context. 
        If legal research is needed, indicate what information would need to be researched.
        If specific legal documents need to be analyzed, indicate what documents would be helpful.
        """
        
        # Use legal-specific parameters
        response = await self.llm_service.generate_response_async(
            prompt=prompt,
            max_tokens=1500,  # Longer responses for legal context
            temperature=0.3,  # Lower temperature for more factual responses
            system_message=self.system_prompt
        )
        
        return response
    
    async def set_jurisdiction(self, jurisdiction: str) -> None:
        """
        Set the jurisdiction for legal context.
        
        Args:
            jurisdiction: Jurisdiction code or name
        """
        self.jurisdiction = jurisdiction
        self.legal_context["jurisdiction"] = jurisdiction
        
        logger.info(f"Legal agent jurisdiction set to: {jurisdiction}")
    
    async def set_legal_specialization(self, specialization: str) -> None:
        """
        Set the legal specialization.
        
        Args:
            specialization: Legal specialization area
        """
        self.legal_specialization = specialization
        self.legal_context["specialization"] = specialization
        
        logger.info(f"Legal agent specialization set to: {specialization}")
    
    async def add_legal_context(self, key: str, value: str) -> None:
        """
        Add legal context information.
        
        Args:
            key: Context key
            value: Context value
        """
        self.legal_context[key] = value
        
        logger.info(f"Added legal context: {key}")
    
    async def perform_legal_research(self, query: str, jurisdiction: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform legal research using available tools.
        
        Args:
            query: Research query
            jurisdiction: Optional jurisdiction override
            
        Returns:
            Dict[str, Any]: Research results
            
        Raises:
            ValueError: If legal research tool not available
        """
        # Use jurisdiction from agent state if not provided
        jurisdiction = jurisdiction or self.jurisdiction
        
        # Find legal research tool
        legal_research_tool = next((t for t in self.tools if t.name == "legal_research"), None)
        
        if not legal_research_tool:
            raise ValueError("Legal research tool not available")
        
        # Use the tool
        result = await legal_research_tool.run(
            query=query,
            jurisdiction=jurisdiction
        )
        
        # Add research to legal context
        self.legal_context["recent_research"] = f"Research on '{query}' in {jurisdiction}"
        
        return result
    
    async def analyze_legal_document(self, document_id: str) -> Dict[str, Any]:
        """
        Analyze a legal document using available tools.
        
        Args:
            document_id: Document ID
            
        Returns:
            Dict[str, Any]: Analysis results
            
        Raises:
            ValueError: If document analysis tool not available
        """
        # Find document analysis tool
        document_analysis_tool = next((t for t in self.tools if t.name == "document_analysis"), None)
        
        if not document_analysis_tool:
            raise ValueError("Document analysis tool not available")
        
        # Use the tool
        result = await document_analysis_tool.run(
            document_id=document_id
        )
        
        # Add analysis to legal context
        self.legal_context["recent_document"] = f"Analysis of document {document_id}"
        
        return result
