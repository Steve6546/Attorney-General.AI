"""
Unit tests for the Document Analysis Tool.
"""

import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import os
import json

# Add the parent directory to the path so we can import the backend modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.tools.document_analysis_tool import DocumentAnalysisTool
from backend.core.llm_service import LLMService


class TestDocumentAnalysisTool(unittest.TestCase):
    """Test cases for the Document Analysis Tool."""

    def setUp(self):
        """Set up test fixtures."""
        self.llm_service_mock = MagicMock(spec=LLMService)
        self.tool = DocumentAnalysisTool(self.llm_service_mock)
    
    def test_initialization(self):
        """Test tool initialization."""
        # Assert tool properties
        self.assertEqual(self.tool.name, "document_analysis")
        self.assertEqual(self.tool.description, "Analyzes legal documents to extract information, summarize content, and identify key elements.")
        self.assertEqual(self.tool.llm_service, self.llm_service_mock)
    
    @patch('backend.tools.document_analysis_tool.os.path.exists')
    @patch('backend.tools.document_analysis_tool.open', new_callable=unittest.mock.mock_open, read_data="This is a test document content")
    async def test_run_summary_analysis(self, mock_open, mock_exists):
        """Test running a summary analysis."""
        # Mock document existence
        mock_exists.return_value = True
        
        # Mock database session and query
        db_mock = MagicMock()
        document_mock = MagicMock()
        document_mock.id = "doc123"
        document_mock.file_path = "/path/to/document.txt"
        document_mock.filename = "document.txt"
        document_mock.content_type = "text/plain"
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.return_value = document_mock
        query_mock.filter.return_value = filter_mock
        db_mock.query.return_value = query_mock
        
        # Mock LLM response
        self.llm_service_mock.generate_response_async.return_value = json.dumps({
            "document_type": "Contract",
            "summary": "This is a contract summary",
            "key_points": ["Point 1", "Point 2"],
            "parties_involved": ["Party A", "Party B"]
        })
        
        # Set database session
        self.tool.db = db_mock
        
        # Run analysis
        result = await self.tool.run(
            document_id="doc123",
            analysis_type="summary"
        )
        
        # Assert result
        self.assertEqual(result["document_id"], "doc123")
        self.assertEqual(result["analysis_type"], "summary")
        self.assertIn("result", result)
        self.assertEqual(result["result"]["document_type"], "Contract")
        self.assertEqual(result["result"]["summary"], "This is a contract summary")
        self.assertEqual(len(result["result"]["key_points"]), 2)
        
        # Assert LLM was called with document content
        self.llm_service_mock.generate_response_async.assert_called_once()
        call_args = self.llm_service_mock.generate_response_async.call_args[1]
        self.assertIn("prompt", call_args)
        self.assertIn("This is a test document content", call_args["prompt"])
        self.assertIn("summary", call_args["prompt"].lower())
    
    @patch('backend.tools.document_analysis_tool.os.path.exists')
    @patch('backend.tools.document_analysis_tool.open', new_callable=unittest.mock.mock_open, read_data="This is a test document content")
    async def test_run_extraction_analysis(self, mock_open, mock_exists):
        """Test running an extraction analysis."""
        # Mock document existence
        mock_exists.return_value = True
        
        # Mock database session and query
        db_mock = MagicMock()
        document_mock = MagicMock()
        document_mock.id = "doc123"
        document_mock.file_path = "/path/to/document.txt"
        document_mock.filename = "document.txt"
        document_mock.content_type = "text/plain"
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.return_value = document_mock
        query_mock.filter.return_value = filter_mock
        db_mock.query.return_value = query_mock
        
        # Mock LLM response
        self.llm_service_mock.generate_response_async.return_value = json.dumps({
            "entities": ["Entity A", "Entity B"],
            "dates": ["2025-01-01", "2025-12-31"],
            "monetary_values": ["$1000", "$2000"],
            "legal_terms": ["Term 1", "Term 2"]
        })
        
        # Set database session
        self.tool.db = db_mock
        
        # Run analysis
        result = await self.tool.run(
            document_id="doc123",
            analysis_type="extraction"
        )
        
        # Assert result
        self.assertEqual(result["document_id"], "doc123")
        self.assertEqual(result["analysis_type"], "extraction")
        self.assertIn("result", result)
        self.assertEqual(len(result["result"]["entities"]), 2)
        self.assertEqual(len(result["result"]["dates"]), 2)
        self.assertEqual(result["result"]["monetary_values"][0], "$1000")
        
        # Assert LLM was called with document content
        self.llm_service_mock.generate_response_async.assert_called_once()
        call_args = self.llm_service_mock.generate_response_async.call_args[1]
        self.assertIn("prompt", call_args)
        self.assertIn("This is a test document content", call_args["prompt"])
        self.assertIn("extraction", call_args["prompt"].lower())
    
    async def test_run_document_not_found(self):
        """Test running analysis with non-existent document."""
        # Mock database session and query
        db_mock = MagicMock()
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.return_value = None
        query_mock.filter.return_value = filter_mock
        db_mock.query.return_value = query_mock
        
        # Set database session
        self.tool.db = db_mock
        
        # Run analysis and expect error
        result = await self.tool.run(
            document_id="nonexistent",
            analysis_type="summary"
        )
        
        # Assert error result
        self.assertEqual(result["document_id"], "nonexistent")
        self.assertEqual(result["analysis_type"], "summary")
        self.assertIn("error", result)
        self.assertIn("not found", result["error"].lower())
        
        # Assert LLM was not called
        self.llm_service_mock.generate_response_async.assert_not_called()
    
    @patch('backend.tools.document_analysis_tool.os.path.exists')
    async def test_run_file_not_found(self, mock_exists):
        """Test running analysis with missing file."""
        # Mock document existence
        mock_exists.return_value = False
        
        # Mock database session and query
        db_mock = MagicMock()
        document_mock = MagicMock()
        document_mock.id = "doc123"
        document_mock.file_path = "/path/to/nonexistent.txt"
        document_mock.filename = "nonexistent.txt"
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.return_value = document_mock
        query_mock.filter.return_value = filter_mock
        db_mock.query.return_value = query_mock
        
        # Set database session
        self.tool.db = db_mock
        
        # Run analysis and expect error
        result = await self.tool.run(
            document_id="doc123",
            analysis_type="summary"
        )
        
        # Assert error result
        self.assertEqual(result["document_id"], "doc123")
        self.assertEqual(result["analysis_type"], "summary")
        self.assertIn("error", result)
        self.assertIn("file not found", result["error"].lower())
        
        # Assert LLM was not called
        self.llm_service_mock.generate_response_async.assert_not_called()
    
    @patch('backend.tools.document_analysis_tool.os.path.exists')
    @patch('backend.tools.document_analysis_tool.open', new_callable=unittest.mock.mock_open, read_data="This is a test document content")
    async def test_run_invalid_analysis_type(self, mock_open, mock_exists):
        """Test running analysis with invalid type."""
        # Mock document existence
        mock_exists.return_value = True
        
        # Mock database session and query
        db_mock = MagicMock()
        document_mock = MagicMock()
        document_mock.id = "doc123"
        document_mock.file_path = "/path/to/document.txt"
        document_mock.filename = "document.txt"
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.return_value = document_mock
        query_mock.filter.return_value = filter_mock
        db_mock.query.return_value = query_mock
        
        # Set database session
        self.tool.db = db_mock
        
        # Run analysis with invalid type
        result = await self.tool.run(
            document_id="doc123",
            analysis_type="invalid_type"
        )
        
        # Assert error result
        self.assertEqual(result["document_id"], "doc123")
        self.assertEqual(result["analysis_type"], "invalid_type")
        self.assertIn("error", result)
        self.assertIn("invalid analysis type", result["error"].lower())
        
        # Assert LLM was not called
        self.llm_service_mock.generate_response_async.assert_not_called()
    
    @patch('backend.tools.document_analysis_tool.os.path.exists')
    @patch('backend.tools.document_analysis_tool.open', new_callable=unittest.mock.mock_open, read_data="This is a test document content")
    async def test_run_llm_error(self, mock_open, mock_exists):
        """Test running analysis with LLM error."""
        # Mock document existence
        mock_exists.return_value = True
        
        # Mock database session and query
        db_mock = MagicMock()
        document_mock = MagicMock()
        document_mock.id = "doc123"
        document_mock.file_path = "/path/to/document.txt"
        document_mock.filename = "document.txt"
        document_mock.content_type = "text/plain"
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.return_value = document_mock
        query_mock.filter.return_value = filter_mock
        db_mock.query.return_value = query_mock
        
        # Mock LLM error
        self.llm_service_mock.generate_response_async.side_effect = Exception("LLM error")
        
        # Set database session
        self.tool.db = db_mock
        
        # Run analysis
        result = await self.tool.run(
            document_id="doc123",
            analysis_type="summary"
        )
        
        # Assert error result
        self.assertEqual(result["document_id"], "doc123")
        self.assertEqual(result["analysis_type"], "summary")
        self.assertIn("error", result)
        self.assertIn("analysis failed", result["error"].lower())
        
        # Assert LLM was called
        self.llm_service_mock.generate_response_async.assert_called_once()


if __name__ == '__main__':
    unittest.main()
