"""
Document Analysis Tool for Attorney-General.AI.

This module provides functionality for analyzing legal documents.
"""

import logging
import os
import json
import asyncio
from typing import List, Dict, Any, Optional
import aiohttp
from bs4 import BeautifulSoup
import re

from backend.core.llm_service import LLMService
from backend.tools.base_tool import BaseTool
from backend.data.models import Document
from backend.data.repository import DocumentRepository
from backend.config.settings import settings

# Configure logging
logger = logging.getLogger(__name__)

class DocumentAnalysisTool(BaseTool):
    """Tool for analyzing legal documents."""
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Initialize the document analysis tool.
        
        Args:
            llm_service: LLM service instance
        """
        super().__init__(
            name="document_analysis",
            description="Analyzes legal documents to extract information, summarize content, and identify key elements."
        )
        self.llm_service = llm_service or LLMService()
        
        logger.info("Document Analysis Tool initialized")
    
    async def run(self, document_id: str, analysis_type: str = "summary", **kwargs) -> Dict[str, Any]:
        """
        Run document analysis.
        
        Args:
            document_id: Document ID
            analysis_type: Type of analysis (summary, extraction, classification, comparison)
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        try:
            # Get document
            document = self.db.query(Document).filter(Document.id == document_id).first()
            if not document:
                return {
                    "document_id": document_id,
                    "analysis_type": analysis_type,
                    "error": "Document not found"
                }
            
            # Check if file exists
            if not os.path.exists(document.file_path):
                return {
                    "document_id": document_id,
                    "analysis_type": analysis_type,
                    "error": "Document file not found"
                }
            
            # Read document content
            with open(document.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Perform analysis based on type
            if analysis_type == "summary":
                result = await self._analyze_summary(document, content)
            elif analysis_type == "extraction":
                result = await self._analyze_extraction(document, content)
            elif analysis_type == "classification":
                result = await self._analyze_classification(document, content)
            elif analysis_type == "comparison":
                comparison_document_id = kwargs.get("comparison_document_id")
                if not comparison_document_id:
                    return {
                        "document_id": document_id,
                        "analysis_type": analysis_type,
                        "error": "Comparison document ID is required for comparison analysis"
                    }
                result = await self._analyze_comparison(document, content, comparison_document_id)
            else:
                return {
                    "document_id": document_id,
                    "analysis_type": analysis_type,
                    "error": "Invalid analysis type"
                }
            
            return {
                "document_id": document_id,
                "analysis_type": analysis_type,
                "result": result
            }
        except Exception as e:
            logger.error(f"Error in document analysis: {str(e)}")
            return {
                "document_id": document_id,
                "analysis_type": analysis_type,
                "error": f"Analysis failed: {str(e)}"
            }
    
    async def _analyze_summary(self, document: Document, content: str) -> Dict[str, Any]:
        """
        Generate a summary of the document.
        
        Args:
            document: Document object
            content: Document content
            
        Returns:
            Dict[str, Any]: Summary analysis
        """
        # Define summary schema
        summary_schema = {
            "document_type": "Type of legal document",
            "summary": "Comprehensive summary of the document",
            "key_points": ["List of key points from the document"],
            "parties_involved": ["List of parties involved, if applicable"],
            "dates": ["List of important dates mentioned"],
            "legal_implications": "Analysis of legal implications"
        }
        
        # Generate summary
        prompt = f"""
        You are a legal document analyst. Analyze the following document and provide a comprehensive summary.
        
        Document Name: {document.filename}
        Document Content:
        {content[:10000]}  # Limit content to avoid token limits
        
        Provide a detailed analysis including:
        1. Type of legal document
        2. Comprehensive summary
        3. Key points
        4. Parties involved (if applicable)
        5. Important dates
        6. Legal implications
        
        Format your response as a structured JSON object.
        """
        
        result = await self.llm_service.generate_response_async(
            prompt=prompt,
            max_tokens=1500,
            temperature=0.3
        )
        
        try:
            # Parse JSON response
            return json.loads(result)
        except json.JSONDecodeError:
            # Fallback to manual parsing if JSON is invalid
            logger.warning(f"Failed to parse JSON from summary response, using fallback parsing")
            
            # Create basic structure
            summary = {
                "document_type": "Unknown",
                "summary": result,
                "key_points": [],
                "parties_involved": [],
                "dates": [],
                "legal_implications": ""
            }
            
            return summary
    
    async def _analyze_extraction(self, document: Document, content: str) -> Dict[str, Any]:
        """
        Extract specific information from the document.
        
        Args:
            document: Document object
            content: Document content
            
        Returns:
            Dict[str, Any]: Extraction analysis
        """
        # Define extraction schema
        extraction_schema = {
            "entities": ["List of entities mentioned"],
            "dates": ["List of dates mentioned"],
            "monetary_values": ["List of monetary values mentioned"],
            "legal_terms": ["List of legal terms and definitions"],
            "obligations": ["List of obligations mentioned"],
            "rights": ["List of rights mentioned"],
            "clauses": ["List of important clauses"]
        }
        
        # Generate extraction
        prompt = f"""
        You are a legal document analyst. Extract specific information from the following document.
        
        Document Name: {document.filename}
        Document Content:
        {content[:10000]}  # Limit content to avoid token limits
        
        Extract the following information:
        1. Entities mentioned (people, companies, organizations)
        2. Dates mentioned
        3. Monetary values mentioned
        4. Legal terms and their definitions
        5. Obligations mentioned
        6. Rights mentioned
        7. Important clauses
        
        Format your response as a structured JSON object.
        """
        
        result = await self.llm_service.generate_response_async(
            prompt=prompt,
            max_tokens=1500,
            temperature=0.3
        )
        
        try:
            # Parse JSON response
            return json.loads(result)
        except json.JSONDecodeError:
            # Fallback to empty structure if JSON is invalid
            logger.warning(f"Failed to parse JSON from extraction response, using fallback parsing")
            
            # Create basic structure
            extraction = {
                "entities": [],
                "dates": [],
                "monetary_values": [],
                "legal_terms": [],
                "obligations": [],
                "rights": [],
                "clauses": []
            }
            
            return extraction
    
    async def _analyze_classification(self, document: Document, content: str) -> Dict[str, Any]:
        """
        Classify the document.
        
        Args:
            document: Document object
            content: Document content
            
        Returns:
            Dict[str, Any]: Classification analysis
        """
        # Define classification schema
        classification_schema = {
            "document_type": "Type of legal document",
            "jurisdiction": "Jurisdiction of the document",
            "legal_domain": "Legal domain (e.g., contract law, criminal law)",
            "confidence": "Confidence score (0-1)",
            "tags": ["List of relevant tags"],
            "risk_level": "Risk level assessment (low, medium, high)",
            "complexity": "Complexity assessment (low, medium, high)"
        }
        
        # Generate classification
        prompt = f"""
        You are a legal document classifier. Classify the following document.
        
        Document Name: {document.filename}
        Document Content:
        {content[:10000]}  # Limit content to avoid token limits
        
        Provide the following classification information:
        1. Document type
        2. Jurisdiction
        3. Legal domain
        4. Confidence score (0-1)
        5. Relevant tags
        6. Risk level assessment (low, medium, high)
        7. Complexity assessment (low, medium, high)
        
        Format your response as a structured JSON object.
        """
        
        result = await self.llm_service.generate_response_async(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.3
        )
        
        try:
            # Parse JSON response
            return json.loads(result)
        except json.JSONDecodeError:
            # Fallback to basic structure if JSON is invalid
            logger.warning(f"Failed to parse JSON from classification response, using fallback parsing")
            
            # Create basic structure
            classification = {
                "document_type": "Unknown",
                "jurisdiction": "Unknown",
                "legal_domain": "Unknown",
                "confidence": 0.5,
                "tags": [],
                "risk_level": "medium",
                "complexity": "medium"
            }
            
            return classification
    
    async def _analyze_comparison(self, document: Document, content: str, comparison_document_id: str) -> Dict[str, Any]:
        """
        Compare two documents.
        
        Args:
            document: Document object
            content: Document content
            comparison_document_id: ID of document to compare with
            
        Returns:
            Dict[str, Any]: Comparison analysis
        """
        try:
            # Get comparison document
            comparison_document = self.db.query(Document).filter(Document.id == comparison_document_id).first()
            if not comparison_document:
                return {
                    "error": f"Comparison document not found: {comparison_document_id}"
                }
            
            # Check if comparison file exists
            if not os.path.exists(comparison_document.file_path):
                return {
                    "error": f"Comparison document file not found: {comparison_document_id}"
                }
            
            # Read comparison document content
            with open(comparison_document.file_path, 'r', encoding='utf-8') as f:
                comparison_content = f.read()
            
            # Define comparison schema
            comparison_schema = {
                "similarities": ["List of similarities between documents"],
                "differences": ["List of differences between documents"],
                "added_clauses": ["List of clauses added in the second document"],
                "removed_clauses": ["List of clauses removed from the first document"],
                "modified_clauses": ["List of clauses modified between documents"],
                "recommendation": "Overall recommendation based on comparison"
            }
            
            # Generate comparison
            prompt = f"""
            You are a legal document analyst. Compare the following two documents and identify similarities, differences, and changes.
            
            Document 1 Name: {document.filename}
            Document 1 Content (first 5000 chars):
            {content[:5000]}
            
            Document 2 Name: {comparison_document.filename}
            Document 2 Content (first 5000 chars):
            {comparison_content[:5000]}
            
            Provide a detailed comparison including:
            1. Similarities between documents
            2. Differences between documents
            3. Clauses added in the second document
            4. Clauses removed from the first document
            5. Clauses modified between documents
            6. Overall recommendation based on comparison
            
            Format your response as a structured JSON object.
            """
            
            result = await self.llm_service.generate_response_async(
                prompt=prompt,
                max_tokens=1500,
                temperature=0.3
            )
            
            try:
                # Parse JSON response
                return json.loads(result)
            except json.JSONDecodeError:
                # Fallback to basic structure if JSON is invalid
                logger.warning(f"Failed to parse JSON from comparison response, using fallback parsing")
                
                # Create basic structure
                comparison = {
                    "similarities": [],
                    "differences": [],
                    "added_clauses": [],
                    "removed_clauses": [],
                    "modified_clauses": [],
                    "recommendation": "Unable to parse structured comparison results."
                }
                
                return comparison
        except Exception as e:
            logger.error(f"Error in document comparison: {str(e)}")
            return {
                "error": f"Comparison failed: {str(e)}"
            }
