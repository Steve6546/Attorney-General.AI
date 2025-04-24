"""
Unit tests for the Legal Agent.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json

# Add the parent directory to the path so we can import the backend modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.agenthub.legal_agent.agent import LegalAgent
from backend.core.llm_service import LLMService
from backend.memory.memory_store import MemoryStore
from backend.tools.legal_research_tool import LegalResearchTool
from backend.tools.document_analysis_tool import DocumentAnalysisTool


class TestLegalAgent(unittest.TestCase):
    """Test cases for the Legal Agent."""

    def setUp(self):
        """Set up test fixtures."""
        self.llm_service_mock = MagicMock(spec=LLMService)
        self.memory_store_mock = MagicMock(spec=MemoryStore)
        self.legal_research_tool = MagicMock(spec=LegalResearchTool)
        self.document_analysis_tool = MagicMock(spec=DocumentAnalysisTool)
        
        # Set tool names
        self.legal_research_tool.name = "legal_research"
        self.document_analysis_tool.name = "document_analysis"
        
        # Create agent
        self.agent = LegalAgent(
            session_id="test_session",
            llm_service=self.llm_service_mock,
            memory_store=self.memory_store_mock,
            tools=[self.legal_research_tool, self.document_analysis_tool]
        )
    
    @patch('backend.utils.prompt_loader.load_prompt')
    def test_initialization(self, mock_load_prompt):
        """Test agent initialization."""
        # Mock prompt loading
        mock_load_prompt.return_value = "Test prompt"
        
        # Create agent
        agent = LegalAgent(
            session_id="test_session",
            llm_service=self.llm_service_mock,
            memory_store=self.memory_store_mock,
            tools=[self.legal_research_tool, self.document_analysis_tool]
        )
        
        # Assert agent properties
        self.assertEqual(agent.session_id, "test_session")
        self.assertEqual(agent.llm_service, self.llm_service_mock)
        self.assertEqual(agent.memory_store, self.memory_store_mock)
        self.assertEqual(len(agent.tools), 2)
        self.assertEqual(agent.system_prompt, "Test prompt")
        self.assertEqual(agent.legal_specialization, "general")
        
        # Assert prompt was loaded
        mock_load_prompt.assert_called_once_with("legal_agent_prompt.yaml")
    
    async def test_process_message(self):
        """Test processing a user message."""
        # Mock LLM response
        self.llm_service_mock.generate_response_async.return_value = "This is a legal response"
        
        # Mock memory store
        self.memory_store_mock.add_memory.return_value = MagicMock()
        
        # Process message
        response = await self.agent.process_message("What is contract law?")
        
        # Assert response
        self.assertEqual(response, "This is a legal response")
        
        # Assert conversation history was updated
        self.assertEqual(len(self.agent.conversation_history), 2)
        self.assertEqual(self.agent.conversation_history[0]["role"], "user")
        self.assertEqual(self.agent.conversation_history[0]["content"], "What is contract law?")
        self.assertEqual(self.agent.conversation_history[1]["role"], "assistant")
        self.assertEqual(self.agent.conversation_history[1]["content"], "This is a legal response")
        
        # Assert memory was stored
        self.memory_store_mock.add_memory.assert_called()
        
        # Assert LLM was called
        self.llm_service_mock.generate_response_async.assert_called_once()
    
    async def test_generate_response(self):
        """Test response generation with legal context."""
        # Mock relevant memories
        memory1 = {"id": "mem1", "content": "Previous discussion about contracts"}
        memory2 = {"id": "mem2", "content": "Previous discussion about torts"}
        
        # Create a patched version of the method
        original_get_memories = self.agent.get_relevant_memories
        self.agent.get_relevant_memories = MagicMock(return_value=[memory1, memory2])
        
        # Add legal context
        self.agent.legal_context = {
            "jurisdiction": "US",
            "specialization": "contract law"
        }
        
        # Mock LLM response
        self.llm_service_mock.generate_response_async.return_value = "Legal response with context"
        
        try:
            # Generate response
            response = await self.agent._generate_response("What is a breach of contract?")
            
            # Assert response
            self.assertEqual(response, "Legal response with context")
            
            # Verify LLM was called with context
            call_args = self.llm_service_mock.generate_response_async.call_args[1]
            self.assertIn("prompt", call_args)
            self.assertIn("What is a breach of contract?", call_args["prompt"])
            self.assertIn("Previous discussion about contracts", call_args["prompt"])
            self.assertIn("jurisdiction: US", call_args["prompt"].lower())
            self.assertIn("specialization: contract law", call_args["prompt"].lower())
        finally:
            # Restore original method
            self.agent.get_relevant_memories = original_get_memories
    
    async def test_set_jurisdiction(self):
        """Test setting jurisdiction."""
        # Set jurisdiction
        await self.agent.set_jurisdiction("UK")
        
        # Assert jurisdiction was set
        self.assertEqual(self.agent.jurisdiction, "UK")
        self.assertEqual(self.agent.legal_context["jurisdiction"], "UK")
    
    async def test_set_legal_specialization(self):
        """Test setting legal specialization."""
        # Set specialization
        await self.agent.set_legal_specialization("intellectual property")
        
        # Assert specialization was set
        self.assertEqual(self.agent.legal_specialization, "intellectual property")
        self.assertEqual(self.agent.legal_context["specialization"], "intellectual property")
    
    async def test_add_legal_context(self):
        """Test adding legal context."""
        # Add context
        await self.agent.add_legal_context("client_type", "corporate")
        
        # Assert context was added
        self.assertEqual(self.agent.legal_context["client_type"], "corporate")
    
    async def test_perform_legal_research(self):
        """Test performing legal research."""
        # Mock tool response
        research_result = {
            "query": "contract breach remedies",
            "jurisdiction": "US",
            "results": [{"title": "Remedies for Breach of Contract", "source": "Legal Source"}]
        }
        self.legal_research_tool.run.return_value = research_result
        
        # Set jurisdiction
        await self.agent.set_jurisdiction("US")
        
        # Perform research
        result = await self.agent.perform_legal_research("contract breach remedies")
        
        # Assert result
        self.assertEqual(result, research_result)
        
        # Assert tool was called
        self.legal_research_tool.run.assert_called_once_with(
            query="contract breach remedies",
            jurisdiction="US"
        )
        
        # Assert context was updated
        self.assertIn("recent_research", self.agent.legal_context)
    
    async def test_perform_legal_research_tool_not_available(self):
        """Test performing legal research without the tool."""
        # Create agent without tools
        agent = LegalAgent(
            session_id="test_session",
            llm_service=self.llm_service_mock,
            memory_store=self.memory_store_mock,
            tools=[]
        )
        
        # Perform research and expect exception
        with self.assertRaises(ValueError):
            await agent.perform_legal_research("contract breach remedies")
    
    async def test_analyze_legal_document(self):
        """Test analyzing a legal document."""
        # Mock tool response
        analysis_result = {
            "document_id": "doc123",
            "analysis_type": "summary",
            "result": {"document_type": "Contract", "summary": "This is a contract summary"}
        }
        self.document_analysis_tool.run.return_value = analysis_result
        
        # Analyze document
        result = await self.agent.analyze_legal_document("doc123")
        
        # Assert result
        self.assertEqual(result, analysis_result)
        
        # Assert tool was called
        self.document_analysis_tool.run.assert_called_once_with(
            document_id="doc123"
        )
        
        # Assert context was updated
        self.assertIn("recent_document", self.agent.legal_context)
    
    async def test_analyze_legal_document_tool_not_available(self):
        """Test analyzing a document without the tool."""
        # Create agent without tools
        agent = LegalAgent(
            session_id="test_session",
            llm_service=self.llm_service_mock,
            memory_store=self.memory_store_mock,
            tools=[]
        )
        
        # Analyze document and expect exception
        with self.assertRaises(ValueError):
            await agent.analyze_legal_document("doc123")


if __name__ == '__main__':
    unittest.main()
