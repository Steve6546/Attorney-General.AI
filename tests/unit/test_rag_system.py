"""
Unit tests for the RAG system.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json
import numpy as np

# Add the parent directory to the path so we can import the backend modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.core.rag_system import RAGSystem
from backend.data.models import Document, DocumentChunk


class TestRAGSystem(unittest.TestCase):
    """Test cases for the RAG system."""

    def setUp(self):
        """Set up test fixtures."""
        self.db_mock = MagicMock()
        self.llm_service_mock = MagicMock()
        self.rag_system = RAGSystem(self.db_mock, self.llm_service_mock)
    
    @patch('backend.core.rag_system.os.path.exists')
    @patch('backend.core.rag_system.open', new_callable=unittest.mock.mock_open, read_data="This is a test document content")
    async def test_index_document_success(self, mock_open, mock_exists):
        """Test successful document indexing."""
        # Mock document
        document_mock = MagicMock()
        document_mock.id = "test_doc_id"
        document_mock.file_path = "/path/to/test_document.txt"
        
        # Mock database query
        self.db_mock.query.return_value.filter.return_value.first.return_value = document_mock
        
        # Mock file existence
        mock_exists.return_value = True
        
        # Mock embedding generation
        self.llm_service_mock.generate_embeddings_async.return_value = [0.1, 0.2, 0.3]
        
        # Call the method
        result = await self.rag_system.index_document("test_doc_id")
        
        # Assert the result
        self.assertEqual(result["document_id"], "test_doc_id")
        self.assertEqual(result["status"], "success")
        self.assertTrue("chunks_created" in result)
        
        # Assert database operations
        self.db_mock.query.assert_called()
        self.db_mock.add.assert_called()
        self.db_mock.commit.assert_called()
        
        # Assert embedding generation
        self.llm_service_mock.generate_embeddings_async.assert_called()
    
    async def test_index_document_not_found(self):
        """Test indexing a non-existent document."""
        # Mock database query
        self.db_mock.query.return_value.filter.return_value.first.return_value = None
        
        # Call the method and expect an error
        result = await self.rag_system.index_document("nonexistent_doc_id")
        
        # Assert the result
        self.assertEqual(result["document_id"], "nonexistent_doc_id")
        self.assertEqual(result["status"], "error")
        self.assertTrue("error" in result)
    
    @patch('backend.core.rag_system.os.path.exists')
    async def test_index_document_file_not_found(self, mock_exists):
        """Test indexing a document with missing file."""
        # Mock document
        document_mock = MagicMock()
        document_mock.id = "test_doc_id"
        document_mock.file_path = "/path/to/nonexistent_file.txt"
        
        # Mock database query
        self.db_mock.query.return_value.filter.return_value.first.return_value = document_mock
        
        # Mock file existence
        mock_exists.return_value = False
        
        # Call the method
        result = await self.rag_system.index_document("test_doc_id")
        
        # Assert the result
        self.assertEqual(result["document_id"], "test_doc_id")
        self.assertEqual(result["status"], "error")
        self.assertTrue("error" in result)
    
    async def test_retrieve_relevant_chunks(self):
        """Test retrieving relevant chunks."""
        # Mock embedding generation
        self.llm_service_mock.generate_embeddings_async.return_value = [0.1, 0.2, 0.3]
        
        # Create mock chunks
        chunk1 = MagicMock()
        chunk1.id = "chunk1"
        chunk1.document_id = "doc1"
        chunk1.content = "Test content 1"
        chunk1.embedding = [0.1, 0.2, 0.3]  # Similar to query
        chunk1.metadata = {}
        
        chunk2 = MagicMock()
        chunk2.id = "chunk2"
        chunk2.document_id = "doc2"
        chunk2.content = "Test content 2"
        chunk2.embedding = [0.9, 0.8, 0.7]  # Less similar to query
        chunk2.metadata = {}
        
        # Mock database queries
        self.db_mock.query.return_value.all.return_value = [chunk1, chunk2]
        
        # Mock document retrieval
        doc1_mock = MagicMock()
        doc1_mock.filename = "document1.txt"
        doc2_mock = MagicMock()
        doc2_mock.filename = "document2.txt"
        
        # Set up document retrieval mock
        self.db_mock.query.return_value.filter.return_value.first.side_effect = [doc1_mock, doc2_mock]
        
        # Call the method
        results = await self.rag_system.retrieve_relevant_chunks("test query")
        
        # Assert the results
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["chunk_id"], "chunk1")
        self.assertEqual(results[0]["document_id"], "doc1")
        self.assertEqual(results[0]["document_name"], "document1.txt")
        
        # Verify the order (most similar first)
        self.assertTrue(results[0]["similarity_score"] > results[1]["similarity_score"])
    
    async def test_generate_augmented_response_with_context(self):
        """Test generating an augmented response with context."""
        # Mock retrieve_relevant_chunks
        chunk1 = {
            "chunk_id": "chunk1",
            "document_id": "doc1",
            "document_name": "document1.txt",
            "content": "Test content 1",
            "similarity_score": 0.95,
            "metadata": {}
        }
        
        chunk2 = {
            "chunk_id": "chunk2",
            "document_id": "doc2",
            "document_name": "document2.txt",
            "content": "Test content 2",
            "similarity_score": 0.85,
            "metadata": {}
        }
        
        # Create a patched version of the method
        original_retrieve = self.rag_system.retrieve_relevant_chunks
        self.rag_system.retrieve_relevant_chunks = MagicMock(return_value=[chunk1, chunk2])
        
        # Mock LLM response
        self.llm_service_mock.generate_response_async.return_value = "This is an augmented response based on the context."
        
        try:
            # Call the method
            result = await self.rag_system.generate_augmented_response("test query")
            
            # Assert the result
            self.assertEqual(result["query"], "test query")
            self.assertEqual(result["response"], "This is an augmented response based on the context.")
            self.assertTrue(result["augmented"])
            self.assertEqual(len(result["sources"]), 2)
            self.assertEqual(result["sources"][0]["document_id"], "doc1")
            self.assertEqual(result["sources"][1]["document_id"], "doc2")
            
            # Verify LLM was called with context
            call_args = self.llm_service_mock.generate_response_async.call_args[1]
            self.assertIn("prompt", call_args)
            self.assertIn("test query", call_args["prompt"])
            self.assertIn("document1.txt", call_args["prompt"])
            self.assertIn("document2.txt", call_args["prompt"])
        finally:
            # Restore original method
            self.rag_system.retrieve_relevant_chunks = original_retrieve
    
    async def test_generate_augmented_response_no_context(self):
        """Test generating a response without context."""
        # Mock retrieve_relevant_chunks to return empty list
        original_retrieve = self.rag_system.retrieve_relevant_chunks
        self.rag_system.retrieve_relevant_chunks = MagicMock(return_value=[])
        
        # Mock LLM response
        self.llm_service_mock.generate_response_async.return_value = "This is a non-augmented response."
        
        try:
            # Call the method
            result = await self.rag_system.generate_augmented_response("test query")
            
            # Assert the result
            self.assertEqual(result["query"], "test query")
            self.assertEqual(result["response"], "This is a non-augmented response.")
            self.assertFalse(result["augmented"])
            self.assertEqual(len(result["sources"]), 0)
            
            # Verify LLM was called without context
            call_args = self.llm_service_mock.generate_response_async.call_args[1]
            self.assertIn("prompt", call_args)
            self.assertEqual(call_args["prompt"], "test query")
        finally:
            # Restore original method
            self.rag_system.retrieve_relevant_chunks = original_retrieve
    
    def test_split_text(self):
        """Test text splitting functionality."""
        # Test with empty text
        chunks = self.rag_system._split_text("", 10, 2)
        self.assertEqual(chunks, [])
        
        # Test with text smaller than chunk size
        chunks = self.rag_system._split_text("Small text", 20, 5)
        self.assertEqual(chunks, ["Small text"])
        
        # Test with text larger than chunk size
        text = "This is a longer text that should be split into multiple chunks with overlap"
        chunks = self.rag_system._split_text(text, 20, 5)
        
        # Check number of chunks
        self.assertTrue(len(chunks) > 1)
        
        # Check overlap
        for i in range(len(chunks) - 1):
            overlap = chunks[i][-5:]
            self.assertTrue(overlap in chunks[i+1])
    
    def test_calculate_similarity(self):
        """Test similarity calculation."""
        # Test with identical vectors
        vec1 = [0.1, 0.2, 0.3]
        vec2 = [0.1, 0.2, 0.3]
        similarity = self.rag_system._calculate_similarity(vec1, vec2)
        self.assertAlmostEqual(similarity, 1.0)
        
        # Test with orthogonal vectors
        vec1 = [1, 0, 0]
        vec2 = [0, 1, 0]
        similarity = self.rag_system._calculate_similarity(vec1, vec2)
        self.assertAlmostEqual(similarity, 0.0)
        
        # Test with opposite vectors
        vec1 = [1, 0, 0]
        vec2 = [-1, 0, 0]
        similarity = self.rag_system._calculate_similarity(vec1, vec2)
        self.assertAlmostEqual(similarity, -1.0)
        
        # Test with zero vector
        vec1 = [0, 0, 0]
        vec2 = [1, 2, 3]
        similarity = self.rag_system._calculate_similarity(vec1, vec2)
        self.assertAlmostEqual(similarity, 0.0)


if __name__ == '__main__':
    unittest.main()
