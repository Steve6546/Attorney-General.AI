"""
Integration tests for the API endpoints.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Add the parent directory to the path so we can import the backend modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.main import app
from backend.data.models import User, Session as ChatSession, Message, Document
from backend.security.security_system import get_password_hash, create_access_token


class TestAPIEndpoints(unittest.TestCase):
    """Integration tests for the API endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        
        # Mock database session
        self.db_mock = MagicMock(spec=Session)
        
        # Create test user
        self.test_user = User(
            id="user1",
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Test User",
            is_active=True
        )
        
        # Create access token
        self.access_token = create_access_token({"sub": self.test_user.username})
        self.headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Patch the get_db dependency
        self.get_db_patcher = patch('backend.api.v1.endpoints.get_db')
        self.get_db_mock = self.get_db_patcher.start()
        self.get_db_mock.return_value = self.db_mock
        
        # Patch the get_current_active_user dependency
        self.get_user_patcher = patch('backend.api.v1.endpoints.get_current_active_user')
        self.get_user_mock = self.get_user_patcher.start()
        self.get_user_mock.return_value = self.test_user
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.get_db_patcher.stop()
        self.get_user_patcher.stop()
    
    def test_root_endpoint(self):
        """Test the root endpoint."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("name", data)
        self.assertIn("version", data)
        self.assertIn("status", data)
        self.assertEqual(data["status"], "running")
    
    def test_health_check(self):
        """Test the health check endpoint."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
    
    def test_login_success(self):
        """Test successful login."""
        # Mock authenticate_user
        with patch('backend.api.v1.endpoints.authenticate_user') as auth_mock:
            auth_mock.return_value = self.test_user
            
            # Send login request
            response = self.client.post(
                "/api/v1/auth/token",
                data={"username": "testuser", "password": "password123"}
            )
            
            # Assert response
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("access_token", data)
            self.assertEqual(data["token_type"], "bearer")
    
    def test_login_failure(self):
        """Test failed login."""
        # Mock authenticate_user
        with patch('backend.api.v1.endpoints.authenticate_user') as auth_mock:
            auth_mock.return_value = None
            
            # Send login request
            response = self.client.post(
                "/api/v1/auth/token",
                data={"username": "testuser", "password": "wrong_password"}
            )
            
            # Assert response
            self.assertEqual(response.status_code, 401)
            data = response.json()
            self.assertIn("detail", data)
    
    def test_register_user(self):
        """Test user registration."""
        # Mock database query for username check
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.return_value = None  # No existing user
        query_mock.filter.return_value = filter_mock
        self.db_mock.query.return_value = query_mock
        
        # Send registration request
        response = self.client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "newpassword",
                "full_name": "New User"
            }
        )
        
        # Assert response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["username"], "newuser")
        self.assertEqual(data["email"], "new@example.com")
        self.assertEqual(data["full_name"], "New User")
        
        # Assert database operations
        self.db_mock.add.assert_called_once()
        self.db_mock.commit.assert_called_once()
    
    def test_register_existing_username(self):
        """Test registration with existing username."""
        # Mock database query for username check
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.side_effect = [self.test_user, None]  # Existing username, no existing email
        query_mock.filter.return_value = filter_mock
        self.db_mock.query.return_value = query_mock
        
        # Send registration request
        response = self.client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",  # Existing username
                "email": "new@example.com",
                "password": "newpassword",
                "full_name": "New User"
            }
        )
        
        # Assert response
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("detail", data)
        self.assertIn("Username already registered", data["detail"])
    
    def test_get_current_user(self):
        """Test getting current user information."""
        # Send request
        response = self.client.get("/api/v1/auth/me", headers=self.headers)
        
        # Assert response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["username"], "testuser")
        self.assertEqual(data["email"], "test@example.com")
        self.assertEqual(data["full_name"], "Test User")
    
    def test_create_session(self):
        """Test creating a new chat session."""
        # Mock session creation
        session_mock = MagicMock()
        session_mock.id = "session1"
        session_mock.title = "Test Session"
        session_mock.created_at = "2025-04-24T12:00:00"
        session_mock.updated_at = "2025-04-24T12:00:00"
        session_mock.is_active = True
        
        # Mock session manager
        with patch('backend.api.v1.endpoints.get_session_manager') as manager_mock:
            manager_instance = MagicMock()
            manager_instance.create_session.return_value = session_mock
            manager_mock.return_value = manager_instance
            
            # Send request
            response = self.client.post(
                "/api/v1/sessions",
                json={"title": "Test Session"},
                headers=self.headers
            )
            
            # Assert response
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["id"], "session1")
            self.assertEqual(data["title"], "Test Session")
            self.assertTrue(data["is_active"])
    
    def test_get_sessions(self):
        """Test getting all user sessions."""
        # Create mock sessions
        session1 = MagicMock()
        session1.id = "session1"
        session1.title = "Session 1"
        session1.created_at = "2025-04-24T12:00:00"
        session1.updated_at = "2025-04-24T12:00:00"
        session1.is_active = True
        
        session2 = MagicMock()
        session2.id = "session2"
        session2.title = "Session 2"
        session2.created_at = "2025-04-24T11:00:00"
        session2.updated_at = "2025-04-24T11:00:00"
        session2.is_active = True
        
        # Mock database query
        query_mock = MagicMock()
        filter_mock = MagicMock()
        order_by_mock = MagicMock()
        order_by_mock.all.return_value = [session1, session2]
        filter_mock.order_by.return_value = order_by_mock
        query_mock.filter.return_value = filter_mock
        self.db_mock.query.return_value = query_mock
        
        # Mock message count query
        count_query_mock = MagicMock()
        count_filter_mock = MagicMock()
        count_filter_mock.count.return_value = 5
        count_query_mock.filter.return_value = count_filter_mock
        self.db_mock.query.side_effect = [query_mock, count_query_mock, count_query_mock]
        
        # Send request
        response = self.client.get("/api/v1/sessions", headers=self.headers)
        
        # Assert response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["id"], "session1")
        self.assertEqual(data[1]["id"], "session2")
    
    def test_get_session(self):
        """Test getting a specific session."""
        # Create mock session
        session_mock = MagicMock()
        session_mock.id = "session1"
        session_mock.title = "Test Session"
        session_mock.created_at = "2025-04-24T12:00:00"
        session_mock.updated_at = "2025-04-24T12:00:00"
        session_mock.is_active = True
        
        # Create mock messages
        message1 = MagicMock()
        message1.id = "msg1"
        message1.role = "user"
        message1.content = "Hello"
        message1.created_at = "2025-04-24T12:01:00"
        
        message2 = MagicMock()
        message2.id = "msg2"
        message2.role = "assistant"
        message2.content = "Hi there"
        message2.created_at = "2025-04-24T12:02:00"
        
        # Mock database queries
        session_query_mock = MagicMock()
        session_filter_mock = MagicMock()
        session_filter_mock.first.return_value = session_mock
        session_query_mock.filter.return_value = session_filter_mock
        
        message_query_mock = MagicMock()
        message_filter_mock = MagicMock()
        message_order_by_mock = MagicMock()
        message_order_by_mock.all.return_value = [message1, message2]
        message_filter_mock.order_by.return_value = message_order_by_mock
        message_query_mock.filter.return_value = message_filter_mock
        
        self.db_mock.query.side_effect = [session_query_mock, message_query_mock]
        
        # Send request
        response = self.client.get("/api/v1/sessions/session1", headers=self.headers)
        
        # Assert response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], "session1")
        self.assertEqual(data["title"], "Test Session")
        self.assertEqual(len(data["messages"]), 2)
        self.assertEqual(data["messages"][0]["role"], "user")
        self.assertEqual(data["messages"][1]["role"], "assistant")
    
    def test_get_session_not_found(self):
        """Test getting a non-existent session."""
        # Mock database query
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.return_value = None
        query_mock.filter.return_value = filter_mock
        self.db_mock.query.return_value = query_mock
        
        # Send request
        response = self.client.get("/api/v1/sessions/nonexistent", headers=self.headers)
        
        # Assert response
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("detail", data)
    
    def test_delete_session(self):
        """Test deleting a session."""
        # Create mock session
        session_mock = MagicMock()
        session_mock.id = "session1"
        
        # Mock database query
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.return_value = session_mock
        query_mock.filter.return_value = filter_mock
        self.db_mock.query.return_value = query_mock
        
        # Mock session manager
        with patch('backend.api.v1.endpoints.get_session_manager') as manager_mock:
            manager_instance = MagicMock()
            manager_instance.delete_session.return_value = True
            manager_mock.return_value = manager_instance
            
            # Send request
            response = self.client.delete("/api/v1/sessions/session1", headers=self.headers)
            
            # Assert response
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data["success"])
    
    def test_create_message(self):
        """Test creating a message in a session."""
        # Create mock session
        session_mock = MagicMock()
        session_mock.id = "session1"
        
        # Mock database query
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.return_value = session_mock
        query_mock.filter.return_value = filter_mock
        self.db_mock.query.return_value = query_mock
        
        # Mock session manager and agent
        with patch('backend.api.v1.endpoints.get_session_manager') as manager_mock:
            manager_instance = MagicMock()
            agent_mock = MagicMock()
            agent_mock.process_message.return_value = "This is a response"
            manager_instance.get_agent.return_value = agent_mock
            manager_mock.return_value = manager_instance
            
            # Send request
            response = self.client.post(
                "/api/v1/sessions/session1/messages",
                json={"content": "Hello"},
                headers=self.headers
            )
            
            # Assert response
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("user_message", data)
            self.assertIn("assistant_message", data)
            self.assertEqual(data["user_message"]["content"], "Hello")
            self.assertEqual(data["assistant_message"]["content"], "This is a response")
    
    def test_upload_document(self):
        """Test uploading a document."""
        # Mock file operations
        with patch('backend.api.v1.endpoints.open', create=True) as mock_open, \
             patch('backend.api.v1.endpoints.os.makedirs') as mock_makedirs:
            
            # Mock file content
            mock_file = MagicMock()
            mock_file.read.return_value = b"Test file content"
            
            # Send request
            response = self.client.post(
                "/api/v1/documents",
                files={"file": ("test.txt", b"Test file content", "text/plain")},
                headers=self.headers
            )
            
            # Assert response
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("id", data)
            self.assertEqual(data["filename"], "test.txt")
            self.assertEqual(data["content_type"], "text/plain")
            self.assertFalse(data["processed"])
            
            # Assert database operations
            self.db_mock.add.assert_called_once()
            self.db_mock.commit.assert_called_once()
    
    def test_get_documents(self):
        """Test getting all user documents."""
        # Create mock documents
        doc1 = MagicMock()
        doc1.id = "doc1"
        doc1.filename = "document1.txt"
        doc1.content_type = "text/plain"
        doc1.size = 100
        doc1.uploaded_at = "2025-04-24T12:00:00"
        doc1.processed = True
        
        doc2 = MagicMock()
        doc2.id = "doc2"
        doc2.filename = "document2.pdf"
        doc2.content_type = "application/pdf"
        doc2.size = 200
        doc2.uploaded_at = "2025-04-24T11:00:00"
        doc2.processed = False
        
        # Mock database query
        query_mock = MagicMock()
        filter_mock = MagicMock()
        order_by_mock = MagicMock()
        order_by_mock.all.return_value = [doc1, doc2]
        filter_mock.order_by.return_value = order_by_mock
        query_mock.filter.return_value = filter_mock
        self.db_mock.query.return_value = query_mock
        
        # Send request
        response = self.client.get("/api/v1/documents", headers=self.headers)
        
        # Assert response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["id"], "doc1")
        self.assertEqual(data[0]["filename"], "document1.txt")
        self.assertEqual(data[1]["id"], "doc2")
        self.assertEqual(data[1]["filename"], "document2.pdf")
    
    def test_index_document(self):
        """Test indexing a document for RAG."""
        # Create mock document
        doc_mock = MagicMock()
        doc_mock.id = "doc1"
        
        # Mock database query
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.return_value = doc_mock
        query_mock.filter.return_value = filter_mock
        self.db_mock.query.return_value = query_mock
        
        # Mock RAG system
        with patch('backend.api.v1.endpoints.RAGSystem') as rag_mock:
            rag_instance = MagicMock()
            rag_instance.index_document.return_value = {
                "document_id": "doc1",
                "chunks_created": 5,
                "status": "success"
            }
            rag_mock.return_value = rag_instance
            
            # Send request
            response = self.client.post("/api/v1/documents/doc1/index", headers=self.headers)
            
            # Assert response
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["document_id"], "doc1")
            self.assertEqual(data["chunks_created"], 5)
            self.assertEqual(data["status"], "success")
    
    def test_legal_research(self):
        """Test performing legal research."""
        # Mock legal research tool
        with patch('backend.api.v1.endpoints.LegalResearchTool') as tool_mock:
            tool_instance = MagicMock()
            tool_instance.run.return_value = {
                "query": "contract law",
                "jurisdiction": "US",
                "results": [{"title": "Contract Law Basics", "source": "Legal Source"}]
            }
            tool_mock.return_value = tool_instance
            
            # Send request
            response = self.client.post(
                "/api/v1/legal-research",
                json={"query": "contract law", "jurisdiction": "US"},
                headers=self.headers
            )
            
            # Assert response
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["query"], "contract law")
            self.assertEqual(data["jurisdiction"], "US")
            self.assertEqual(len(data["results"]), 1)
    
    def test_document_analysis(self):
        """Test analyzing a document."""
        # Create mock document
        doc_mock = MagicMock()
        doc_mock.id = "doc1"
        
        # Mock database query
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.return_value = doc_mock
        query_mock.filter.return_value = filter_mock
        self.db_mock.query.return_value = query_mock
        
        # Mock document analysis tool
        with patch('backend.api.v1.endpoints.DocumentAnalysisTool') as tool_mock:
            tool_instance = MagicMock()
            tool_instance.run.return_value = {
                "document_id": "doc1",
                "analysis_type": "summary",
                "result": {"document_type": "Contract", "summary": "This is a contract summary"}
            }
            tool_mock.return_value = tool_instance
            
            # Send request
            response = self.client.post(
                "/api/v1/document-analysis",
                json={"document_id": "doc1", "analysis_type": "summary"},
                headers=self.headers
            )
            
            # Assert response
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["document_id"], "doc1")
            self.assertEqual(data["analysis_type"], "summary")
            self.assertEqual(data["result"]["document_type"], "Contract")
    
    def test_rag_query(self):
        """Test querying the RAG system."""
        # Mock RAG system
        with patch('backend.api.v1.endpoints.RAGSystem') as rag_mock:
            rag_instance = MagicMock()
            rag_instance.generate_augmented_response.return_value = {
                "query": "What is a contract?",
                "response": "A contract is a legally binding agreement...",
                "sources": [{"document_id": "doc1", "document_name": "Contract Law.pdf"}],
                "augmented": True
            }
            rag_mock.return_value = rag_instance
            
            # Send request
            response = self.client.post(
                "/api/v1/rag/query",
                json={"query": "What is a contract?"},
                headers=self.headers
            )
            
            # Assert response
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["query"], "What is a contract?")
            self.assertIn("A contract is a legally binding agreement", data["response"])
            self.assertTrue(data["augmented"])
            self.assertEqual(len(data["sources"]), 1)


if __name__ == '__main__':
    unittest.main()
