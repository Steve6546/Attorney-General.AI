"""
Unit tests for the Memory Store.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json
from datetime import datetime, timedelta
import numpy as np

# Add the parent directory to the path so we can import the backend modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.memory.memory_store import MemoryStore
from backend.data.models import MemoryItem


class TestMemoryStore(unittest.TestCase):
    """Test cases for the Memory Store."""

    def setUp(self):
        """Set up test fixtures."""
        self.db_mock = MagicMock()
        self.llm_service_mock = MagicMock()
        self.memory_store = MemoryStore(self.db_mock, self.llm_service_mock)
    
    async def test_add_memory(self):
        """Test adding a memory item."""
        # Mock embedding generation
        self.llm_service_mock.generate_embeddings_async.return_value = [0.1, 0.2, 0.3]
        
        # Call the method
        memory_item = await self.memory_store.add_memory(
            session_id="test_session",
            content="Test memory content",
            importance=0.8,
            memory_type="short_term"
        )
        
        # Assert database operations
        self.db_mock.add.assert_called_once()
        self.db_mock.commit.assert_called_once()
        self.db_mock.refresh.assert_called_once()
        
        # Assert embedding generation
        self.llm_service_mock.generate_embeddings_async.assert_called_once_with("Test memory content")
    
    async def test_get_relevant_memories(self):
        """Test retrieving relevant memories."""
        # Mock embedding generation
        self.llm_service_mock.generate_embeddings_async.return_value = [0.1, 0.2, 0.3]
        
        # Create mock memory items
        memory1 = MagicMock()
        memory1.id = "mem1"
        memory1.content = "Memory content 1"
        memory1.embedding = [0.1, 0.2, 0.3]  # Similar to query
        memory1.importance = 0.8
        memory1.created_at = datetime.utcnow()
        memory1.memory_type = "short_term"
        
        memory2 = MagicMock()
        memory2.id = "mem2"
        memory2.content = "Memory content 2"
        memory2.embedding = [0.9, 0.8, 0.7]  # Less similar to query
        memory2.importance = 0.5
        memory2.created_at = datetime.utcnow()
        memory2.memory_type = "short_term"
        
        # Mock database query
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.all.return_value = [memory1, memory2]
        query_mock.filter.return_value = filter_mock
        self.db_mock.query.return_value = query_mock
        
        # Call the method
        results = await self.memory_store.get_relevant_memories(
            session_id="test_session",
            query="Test query",
            limit=2
        )
        
        # Assert the results
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].id, "mem1")  # Most similar should be first
        
        # Assert embedding generation
        self.llm_service_mock.generate_embeddings_async.assert_called_once_with("Test query")
        
        # Assert access count was updated
        self.assertEqual(memory1.access_count, 1)
        self.assertEqual(memory2.access_count, 1)
    
    async def test_get_relevant_memories_with_memory_type_filter(self):
        """Test retrieving relevant memories with memory type filter."""
        # Mock embedding generation
        self.llm_service_mock.generate_embeddings_async.return_value = [0.1, 0.2, 0.3]
        
        # Create mock memory items
        memory1 = MagicMock()
        memory1.id = "mem1"
        memory1.content = "Memory content 1"
        memory1.embedding = [0.1, 0.2, 0.3]
        memory1.importance = 0.8
        memory1.created_at = datetime.utcnow()
        memory1.memory_type = "long_term"
        
        # Mock database query
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.all.return_value = [memory1]
        query_mock.filter.return_value = filter_mock
        self.db_mock.query.return_value = query_mock
        
        # Call the method with memory_type filter
        results = await self.memory_store.get_relevant_memories(
            session_id="test_session",
            query="Test query",
            limit=5,
            memory_type="long_term"
        )
        
        # Assert the results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "mem1")
        
        # Assert query was filtered by memory_type
        query_mock.filter.assert_called()
    
    def test_get_all_memories(self):
        """Test retrieving all memories for a session."""
        # Create mock memory items
        memory1 = MagicMock()
        memory1.id = "mem1"
        memory1.created_at = datetime.utcnow()
        
        memory2 = MagicMock()
        memory2.id = "mem2"
        memory2.created_at = datetime.utcnow() - timedelta(minutes=5)
        
        # Mock database query
        query_mock = MagicMock()
        filter_mock = MagicMock()
        order_by_mock = MagicMock()
        order_by_mock.all.return_value = [memory1, memory2]
        filter_mock.order_by.return_value = order_by_mock
        query_mock.filter.return_value = filter_mock
        self.db_mock.query.return_value = query_mock
        
        # Call the method
        results = self.memory_store.get_all_memories(session_id="test_session")
        
        # Assert the results
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].id, "mem1")
        self.assertEqual(results[1].id, "mem2")
    
    def test_delete_memory(self):
        """Test deleting a memory item."""
        # Mock memory item
        memory_mock = MagicMock()
        memory_mock.id = "mem1"
        
        # Mock database query
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.return_value = memory_mock
        query_mock.filter.return_value = filter_mock
        self.db_mock.query.return_value = query_mock
        
        # Call the method
        result = self.memory_store.delete_memory("mem1")
        
        # Assert the result
        self.assertTrue(result)
        
        # Assert database operations
        self.db_mock.delete.assert_called_once_with(memory_mock)
        self.db_mock.commit.assert_called_once()
    
    def test_delete_memory_not_found(self):
        """Test deleting a non-existent memory item."""
        # Mock database query
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.return_value = None
        query_mock.filter.return_value = filter_mock
        self.db_mock.query.return_value = query_mock
        
        # Call the method
        result = self.memory_store.delete_memory("nonexistent_mem")
        
        # Assert the result
        self.assertFalse(result)
        
        # Assert database operations
        self.db_mock.delete.assert_not_called()
    
    def test_clear_session_memories(self):
        """Test clearing all memories for a session."""
        # Mock database query
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.delete.return_value = 5  # 5 items deleted
        query_mock.filter.return_value = filter_mock
        self.db_mock.query.return_value = query_mock
        
        # Call the method
        result = self.memory_store.clear_session_memories("test_session")
        
        # Assert the result
        self.assertEqual(result, 5)
        
        # Assert database operations
        filter_mock.delete.assert_called_once()
        self.db_mock.commit.assert_called_once()
    
    async def test_promote_to_long_term(self):
        """Test promoting a memory item to long-term memory."""
        # Mock memory item
        memory_mock = MagicMock()
        memory_mock.id = "mem1"
        memory_mock.memory_type = "short_term"
        memory_mock.importance = 0.5
        
        # Mock database query
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.return_value = memory_mock
        query_mock.filter.return_value = filter_mock
        self.db_mock.query.return_value = query_mock
        
        # Call the method
        result = await self.memory_store.promote_to_long_term("mem1")
        
        # Assert the result
        self.assertEqual(result, memory_mock)
        
        # Assert memory was updated
        self.assertEqual(memory_mock.memory_type, "long_term")
        self.assertGreaterEqual(memory_mock.importance, 0.7)
        
        # Assert database operations
        self.db_mock.commit.assert_called_once()
        self.db_mock.refresh.assert_called_once_with(memory_mock)
    
    async def test_promote_to_long_term_not_found(self):
        """Test promoting a non-existent memory item."""
        # Mock database query
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.return_value = None
        query_mock.filter.return_value = filter_mock
        self.db_mock.query.return_value = query_mock
        
        # Call the method
        result = await self.memory_store.promote_to_long_term("nonexistent_mem")
        
        # Assert the result
        self.assertIsNone(result)
        
        # Assert database operations
        self.db_mock.commit.assert_not_called()
    
    def test_calculate_similarity(self):
        """Test similarity calculation."""
        # Test with identical vectors
        vec1 = [0.1, 0.2, 0.3]
        vec2 = [0.1, 0.2, 0.3]
        similarity = self.memory_store._calculate_similarity(vec1, vec2)
        self.assertAlmostEqual(similarity, 1.0)
        
        # Test with orthogonal vectors
        vec1 = [1, 0, 0]
        vec2 = [0, 1, 0]
        similarity = self.memory_store._calculate_similarity(vec1, vec2)
        self.assertAlmostEqual(similarity, 0.0)
        
        # Test with opposite vectors
        vec1 = [1, 0, 0]
        vec2 = [-1, 0, 0]
        similarity = self.memory_store._calculate_similarity(vec1, vec2)
        self.assertAlmostEqual(similarity, -1.0)
        
        # Test with zero vector
        vec1 = [0, 0, 0]
        vec2 = [1, 2, 3]
        similarity = self.memory_store._calculate_similarity(vec1, vec2)
        self.assertAlmostEqual(similarity, 0.0)


if __name__ == '__main__':
    unittest.main()
