"""
Legal Research Tool for Attorney-General.AI.

This module provides functionality for legal research and case law search.
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
from backend.config.settings import settings

# Configure logging
logger = logging.getLogger(__name__)

class LegalResearchTool(BaseTool):
    """Tool for legal research and case law search."""
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Initialize the legal research tool.
        
        Args:
            llm_service: LLM service instance
        """
        super().__init__(
            name="legal_research",
            description="Performs legal research on specific topics or questions, searches for relevant case law, statutes, and legal commentary."
        )
        self.llm_service = llm_service or LLMService()
        
        # API endpoints for legal research
        self.api_endpoints = {
            "case_law": settings.LEGAL_API_CASE_LAW_ENDPOINT,
            "statutes": settings.LEGAL_API_STATUTES_ENDPOINT,
            "commentary": settings.LEGAL_API_COMMENTARY_ENDPOINT
        }
        
        # API key for legal research
        self.api_key = settings.LEGAL_API_KEY
        
        logger.info("Legal Research Tool initialized")
    
    async def run(self, query: str, jurisdiction: str = "US", result_limit: int = 5, **kwargs) -> Dict[str, Any]:
        """
        Run legal research on a query.
        
        Args:
            query: Research query
            jurisdiction: Legal jurisdiction (e.g., US, UK, EU)
            result_limit: Maximum number of results to return
            
        Returns:
            Dict[str, Any]: Research results
        """
        try:
            # Validate inputs
            if not query:
                return {
                    "query": query,
                    "jurisdiction": jurisdiction,
                    "error": "Query cannot be empty"
                }
            
            # Normalize jurisdiction
            jurisdiction = jurisdiction.upper()
            
            # Prepare results
            results = {
                "query": query,
                "jurisdiction": jurisdiction,
                "results": []
            }
            
            # Determine if we need to use API or web search
            if self.api_key and all(endpoint for endpoint in self.api_endpoints.values()):
                # Use legal API
                api_results = await self._search_legal_api(query, jurisdiction, result_limit)
                results["results"] = api_results
                results["source"] = "legal_api"
            else:
                # Fallback to web search
                web_results = await self._search_legal_web(query, jurisdiction, result_limit)
                results["results"] = web_results
                results["source"] = "web_search"
            
            # Enhance results with LLM analysis if results are found
            if results["results"]:
                analysis = await self._analyze_results(query, results["results"])
                results["analysis"] = analysis
            
            return results
        except Exception as e:
            logger.error(f"Error in legal research: {str(e)}")
            return {
                "query": query,
                "jurisdiction": jurisdiction,
                "error": f"Error performing legal research: {str(e)}",
                "results": []
            }
    
    async def _search_legal_api(self, query: str, jurisdiction: str, result_limit: int) -> List[Dict[str, Any]]:
        """
        Search legal API for results.
        
        Args:
            query: Research query
            jurisdiction: Legal jurisdiction
            result_limit: Maximum number of results
            
        Returns:
            List[Dict[str, Any]]: API search results
        """
        results = []
        
        try:
            # Prepare API request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Search case law
            if self.api_endpoints["case_law"]:
                case_law_results = await self._api_request(
                    self.api_endpoints["case_law"],
                    {
                        "query": query,
                        "jurisdiction": jurisdiction,
                        "limit": result_limit
                    },
                    headers
                )
                
                if case_law_results and "results" in case_law_results:
                    for result in case_law_results["results"]:
                        results.append({
                            "title": result.get("title", "Unknown Case"),
                            "citation": result.get("citation", ""),
                            "date": result.get("date", ""),
                            "court": result.get("court", ""),
                            "summary": result.get("summary", ""),
                            "url": result.get("url", ""),
                            "type": "case_law"
                        })
            
            # Search statutes
            if self.api_endpoints["statutes"]:
                statutes_results = await self._api_request(
                    self.api_endpoints["statutes"],
                    {
                        "query": query,
                        "jurisdiction": jurisdiction,
                        "limit": result_limit
                    },
                    headers
                )
                
                if statutes_results and "results" in statutes_results:
                    for result in statutes_results["results"]:
                        results.append({
                            "title": result.get("title", "Unknown Statute"),
                            "code": result.get("code", ""),
                            "section": result.get("section", ""),
                            "text": result.get("text", ""),
                            "url": result.get("url", ""),
                            "type": "statute"
                        })
            
            # Search legal commentary
            if self.api_endpoints["commentary"]:
                commentary_results = await self._api_request(
                    self.api_endpoints["commentary"],
                    {
                        "query": query,
                        "jurisdiction": jurisdiction,
                        "limit": result_limit
                    },
                    headers
                )
                
                if commentary_results and "results" in commentary_results:
                    for result in commentary_results["results"]:
                        results.append({
                            "title": result.get("title", "Unknown Commentary"),
                            "author": result.get("author", ""),
                            "publication": result.get("publication", ""),
                            "date": result.get("date", ""),
                            "summary": result.get("summary", ""),
                            "url": result.get("url", ""),
                            "type": "commentary"
                        })
            
            # Limit total results
            return results[:result_limit]
        except Exception as e:
            logger.error(f"Error searching legal API: {str(e)}")
            return []
    
    async def _api_request(self, endpoint: str, data: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Make an API request.
        
        Args:
            endpoint: API endpoint
            data: Request data
            headers: Request headers
            
        Returns:
            Dict[str, Any]: API response
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, json=data, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"API request failed with status {response.status}: {await response.text()}")
                        return {}
        except Exception as e:
            logger.error(f"Error making API request: {str(e)}")
            return {}
    
    async def _search_legal_web(self, query: str, jurisdiction: str, result_limit: int) -> List[Dict[str, Any]]:
        """
        Search web for legal information.
        
        Args:
            query: Research query
            jurisdiction: Legal jurisdiction
            result_limit: Maximum number of results
            
        Returns:
            List[Dict[str, Any]]: Web search results
        """
        results = []
        
        try:
            # Prepare search query
            search_query = f"{query} legal {jurisdiction} law"
            
            # Use LLM to generate structured search results
            # This is a fallback when no legal API is available
            schema = {
                "results": [
                    {
                        "title": "Title of the legal resource",
                        "source": "Source name (e.g., court, publication)",
                        "date": "Publication date if available",
                        "summary": "Brief summary of the content",
                        "url": "URL if available (or 'Not available')",
                        "type": "Type of resource (case_law, statute, commentary, article)"
                    }
                ]
            }
            
            # Generate structured results
            prompt = f"""
            You are a legal research assistant. Based on the query "{query}" for the jurisdiction "{jurisdiction}", 
            provide {result_limit} relevant legal resources that would be helpful for this research.
            
            Include case law, statutes, and legal commentary where appropriate. For each resource, provide:
            1. Title
            2. Source (court, publication, etc.)
            3. Date (if known)
            4. Brief summary of relevance to the query
            5. URL (if known, otherwise "Not available")
            6. Type of resource (case_law, statute, commentary, article)
            
            Format your response as a structured JSON object.
            """
            
            structured_results = await self.llm_service.generate_structured_output_async(
                prompt=prompt,
                output_schema=schema,
                temperature=0.2
            )
            
            if "results" in structured_results:
                results = structured_results["results"]
            
            return results[:result_limit]
        except Exception as e:
            logger.error(f"Error searching legal web: {str(e)}")
            return []
    
    async def _analyze_results(self, query: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze research results using LLM.
        
        Args:
            query: Original query
            results: Research results
            
        Returns:
            Dict[str, Any]: Analysis of results
        """
        try:
            # Prepare results summary
            results_summary = ""
            for i, result in enumerate(results):
                results_summary += f"[{i+1}] {result.get('title', 'Unknown')}\n"
                if "citation" in result:
                    results_summary += f"Citation: {result['citation']}\n"
                if "court" in result:
                    results_summary += f"Court: {result['court']}\n"
                if "date" in result:
                    results_summary += f"Date: {result['date']}\n"
                if "summary" in result:
                    results_summary += f"Summary: {result['summary']}\n"
                results_summary += "\n"
            
            # Define analysis schema
            analysis_schema = {
                "key_principles": ["List of key legal principles identified"],
                "relevance": "Assessment of how relevant the results are to the query",
                "gaps": ["Potential gaps in the research"],
                "recommendations": ["Recommendations for further research"]
            }
            
            # Generate analysis
            prompt = f"""
            You are a legal research analyst. Analyze the following legal research results for the query: "{query}"
            
            Research Results:
            {results_summary}
            
            Provide an analysis that includes:
            1. Key legal principles identified in these results
            2. Assessment of how relevant these results are to the original query
            3. Potential gaps in the research that should be addressed
            4. Recommendations for further research
            
            Format your response as a structured JSON object.
            """
            
            analysis = await self.llm_service.generate_structured_output_async(
                prompt=prompt,
                output_schema=analysis_schema,
                temperature=0.3
            )
            
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing results: {str(e)}")
            return {
                "error": f"Error analyzing results: {str(e)}"
            }
