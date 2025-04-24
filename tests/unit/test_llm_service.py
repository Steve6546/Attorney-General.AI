"""
Unit tests for the LLM Service.
"""

import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import os
import json
import asyncio

# Add the parent directory to the path so we can import the backend modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.core.llm_service import LLMService
from backend.config.settings import settings


class TestLLMService(unittest.TestCase):
    """Test cases for the LLM Service."""

    def setUp(self):
        """Set up test fixtures."""
        self.llm_service = LLMService()
    
    @patch('backend.core.llm_service.openai.Completion.create')
    def test_generate_response(self, mock_completion):
        """Test generating a response."""
        # Mock OpenAI response
        mock_completion.return_value = {
            "choices": [{"text": "This is a test response"}],
            "usage": {"total_tokens": 10}
        }
        
        # Generate response
        response = self.llm_service.generate_response(
            prompt="Test prompt",
            max_tokens=100,
            temperature=0.7
        )
        
        # Assert response
        self.assertEqual(response, "This is a test response")
        
        # Assert OpenAI was called with correct parameters
        mock_completion.assert_called_once()
        args, kwargs = mock_completion.call_args
        self.assertEqual(kwargs["prompt"], "Test prompt")
        self.assertEqual(kwargs["max_tokens"], 100)
        self.assertEqual(kwargs["temperature"], 0.7)
        self.assertEqual(kwargs["model"], settings.LLM_MODEL)
    
    @patch('backend.core.llm_service.openai.Completion.create')
    def test_generate_response_with_error(self, mock_completion):
        """Test generating a response with an error."""
        # Mock OpenAI error
        mock_completion.side_effect = Exception("API error")
        
        # Generate response and expect fallback
        response = self.llm_service.generate_response(
            prompt="Test prompt",
            max_tokens=100,
            temperature=0.7
        )
        
        # Assert fallback response
        self.assertIn("I apologize", response.lower())
        self.assertIn("error", response.lower())
    
    @patch('backend.core.llm_service.openai.Completion.acreate')
    async def test_generate_response_async(self, mock_acreate):
        """Test generating a response asynchronously."""
        # Mock OpenAI response
        mock_acreate.return_value = {
            "choices": [{"text": "This is an async test response"}],
            "usage": {"total_tokens": 10}
        }
        
        # Generate response
        response = await self.llm_service.generate_response_async(
            prompt="Test prompt",
            max_tokens=100,
            temperature=0.7
        )
        
        # Assert response
        self.assertEqual(response, "This is an async test response")
        
        # Assert OpenAI was called with correct parameters
        mock_acreate.assert_called_once()
        args, kwargs = mock_acreate.call_args
        self.assertEqual(kwargs["prompt"], "Test prompt")
        self.assertEqual(kwargs["max_tokens"], 100)
        self.assertEqual(kwargs["temperature"], 0.7)
        self.assertEqual(kwargs["model"], settings.LLM_MODEL)
    
    @patch('backend.core.llm_service.openai.Completion.acreate')
    async def test_generate_response_async_with_error(self, mock_acreate):
        """Test generating a response asynchronously with an error."""
        # Mock OpenAI error
        mock_acreate.side_effect = Exception("API error")
        
        # Generate response and expect fallback
        response = await self.llm_service.generate_response_async(
            prompt="Test prompt",
            max_tokens=100,
            temperature=0.7
        )
        
        # Assert fallback response
        self.assertIn("I apologize", response.lower())
        self.assertIn("error", response.lower())
    
    @patch('backend.core.llm_service.openai.Embedding.create')
    def test_generate_embeddings(self, mock_embedding):
        """Test generating embeddings."""
        # Mock OpenAI response
        mock_embedding.return_value = {
            "data": [{"embedding": [0.1, 0.2, 0.3]}],
            "usage": {"total_tokens": 5}
        }
        
        # Generate embeddings
        embeddings = self.llm_service.generate_embeddings("Test text")
        
        # Assert embeddings
        self.assertEqual(embeddings, [0.1, 0.2, 0.3])
        
        # Assert OpenAI was called with correct parameters
        mock_embedding.assert_called_once()
        args, kwargs = mock_embedding.call_args
        self.assertEqual(kwargs["input"], "Test text")
        self.assertEqual(kwargs["model"], settings.EMBEDDING_MODEL)
    
    @patch('backend.core.llm_service.openai.Embedding.create')
    def test_generate_embeddings_with_error(self, mock_embedding):
        """Test generating embeddings with an error."""
        # Mock OpenAI error
        mock_embedding.side_effect = Exception("API error")
        
        # Generate embeddings and expect empty list
        embeddings = self.llm_service.generate_embeddings("Test text")
        
        # Assert empty embeddings
        self.assertEqual(embeddings, [])
    
    @patch('backend.core.llm_service.openai.Embedding.acreate')
    async def test_generate_embeddings_async(self, mock_acreate):
        """Test generating embeddings asynchronously."""
        # Mock OpenAI response
        mock_acreate.return_value = {
            "data": [{"embedding": [0.1, 0.2, 0.3]}],
            "usage": {"total_tokens": 5}
        }
        
        # Generate embeddings
        embeddings = await self.llm_service.generate_embeddings_async("Test text")
        
        # Assert embeddings
        self.assertEqual(embeddings, [0.1, 0.2, 0.3])
        
        # Assert OpenAI was called with correct parameters
        mock_acreate.assert_called_once()
        args, kwargs = mock_acreate.call_args
        self.assertEqual(kwargs["input"], "Test text")
        self.assertEqual(kwargs["model"], settings.EMBEDDING_MODEL)
    
    @patch('backend.core.llm_service.openai.Embedding.acreate')
    async def test_generate_embeddings_async_with_error(self, mock_acreate):
        """Test generating embeddings asynchronously with an error."""
        # Mock OpenAI error
        mock_acreate.side_effect = Exception("API error")
        
        # Generate embeddings and expect empty list
        embeddings = await self.llm_service.generate_embeddings_async("Test text")
        
        # Assert empty embeddings
        self.assertEqual(embeddings, [])
    
    def test_format_prompt(self):
        """Test formatting a prompt."""
        # Format prompt with system message
        prompt = self.llm_service._format_prompt(
            system="You are a helpful assistant.",
            user="Hello",
            assistant=None
        )
        
        # Assert prompt format
        self.assertIn("You are a helpful assistant.", prompt)
        self.assertIn("Hello", prompt)
    
    def test_format_prompt_with_history(self):
        """Test formatting a prompt with conversation history."""
        # Format prompt with history
        prompt = self.llm_service._format_prompt(
            system="You are a helpful assistant.",
            user="How are you?",
            assistant="I'm doing well, thank you!",
            history=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ]
        )
        
        # Assert prompt format
        self.assertIn("You are a helpful assistant.", prompt)
        self.assertIn("Hello", prompt)
        self.assertIn("Hi there!", prompt)
        self.assertIn("How are you?", prompt)
        self.assertIn("I'm doing well, thank you!", prompt)


if __name__ == '__main__':
    unittest.main()
