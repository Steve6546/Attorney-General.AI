"""
Unit tests for the Security System.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json
from datetime import datetime, timedelta
import jwt

# Add the parent directory to the path so we can import the backend modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.security.security_system import (
    get_password_hash, verify_password, create_access_token,
    decode_token, authenticate_user, get_current_user
)
from backend.data.models import User


class TestSecuritySystem(unittest.TestCase):
    """Test cases for the Security System."""

    def setUp(self):
        """Set up test fixtures."""
        self.db_mock = MagicMock()
        
        # Create a test user
        self.test_user = User(
            id="user1",
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Test User",
            is_active=True
        )
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        # Hash a password
        password = "secure_password123"
        hashed = get_password_hash(password)
        
        # Verify the password
        self.assertTrue(verify_password(password, hashed))
        
        # Verify incorrect password fails
        self.assertFalse(verify_password("wrong_password", hashed))
        
        # Verify different hashes for same password
        hashed2 = get_password_hash(password)
        self.assertNotEqual(hashed, hashed2)
    
    def test_create_access_token(self):
        """Test creating an access token."""
        # Create token data
        data = {"sub": "testuser"}
        
        # Create token with default expiry
        token = create_access_token(data)
        
        # Verify token is a string
        self.assertIsInstance(token, str)
        
        # Decode token and verify data
        decoded = jwt.decode(token, "secret_key", algorithms=["HS256"])
        self.assertEqual(decoded["sub"], "testuser")
        self.assertIn("exp", decoded)
        
        # Create token with custom expiry
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data, expires_delta)
        
        # Decode token and verify expiry
        decoded = jwt.decode(token, "secret_key", algorithms=["HS256"])
        self.assertEqual(decoded["sub"], "testuser")
        self.assertIn("exp", decoded)
    
    def test_decode_token(self):
        """Test decoding an access token."""
        # Create a token
        token_data = {"sub": "testuser"}
        token = create_access_token(token_data)
        
        # Decode the token
        payload = decode_token(token)
        
        # Verify payload
        self.assertEqual(payload["sub"], "testuser")
    
    def test_decode_token_expired(self):
        """Test decoding an expired token."""
        # Create an expired token
        token_data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=-10)  # Expired 10 minutes ago
        token = create_access_token(token_data, expires_delta)
        
        # Attempt to decode the token and expect an exception
        with self.assertRaises(jwt.PyJWTError):
            decode_token(token)
    
    def test_authenticate_user_success(self):
        """Test successful user authentication."""
        # Mock database query
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.return_value = self.test_user
        query_mock.filter.return_value = filter_mock
        self.db_mock.query.return_value = query_mock
        
        # Authenticate user
        user = authenticate_user(self.db_mock, "testuser", "password123")
        
        # Verify user was authenticated
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "testuser")
    
    def test_authenticate_user_wrong_password(self):
        """Test authentication with wrong password."""
        # Mock database query
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.return_value = self.test_user
        query_mock.filter.return_value = filter_mock
        self.db_mock.query.return_value = query_mock
        
        # Authenticate user with wrong password
        user = authenticate_user(self.db_mock, "testuser", "wrong_password")
        
        # Verify authentication failed
        self.assertIsNone(user)
    
    def test_authenticate_user_not_found(self):
        """Test authentication with non-existent user."""
        # Mock database query
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.return_value = None
        query_mock.filter.return_value = filter_mock
        self.db_mock.query.return_value = query_mock
        
        # Authenticate non-existent user
        user = authenticate_user(self.db_mock, "nonexistent", "password123")
        
        # Verify authentication failed
        self.assertIsNone(user)
    
    def test_authenticate_user_inactive(self):
        """Test authentication with inactive user."""
        # Create inactive user
        inactive_user = User(
            id="user2",
            username="inactive",
            email="inactive@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Inactive User",
            is_active=False
        )
        
        # Mock database query
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.return_value = inactive_user
        query_mock.filter.return_value = filter_mock
        self.db_mock.query.return_value = query_mock
        
        # Authenticate inactive user
        user = authenticate_user(self.db_mock, "inactive", "password123")
        
        # Verify authentication failed
        self.assertIsNone(user)
    
    @patch('backend.security.security_system.decode_token')
    def test_get_current_user(self, mock_decode_token):
        """Test getting current user from token."""
        # Mock token decoding
        mock_decode_token.return_value = {"sub": "testuser"}
        
        # Mock database query
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.return_value = self.test_user
        query_mock.filter.return_value = filter_mock
        self.db_mock.query.return_value = query_mock
        
        # Get current user
        user = get_current_user("fake_token", self.db_mock)
        
        # Verify user was retrieved
        self.assertEqual(user, self.test_user)
        
        # Verify token was decoded
        mock_decode_token.assert_called_once_with("fake_token")
    
    @patch('backend.security.security_system.decode_token')
    def test_get_current_user_not_found(self, mock_decode_token):
        """Test getting non-existent user from token."""
        # Mock token decoding
        mock_decode_token.return_value = {"sub": "nonexistent"}
        
        # Mock database query
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.return_value = None
        query_mock.filter.return_value = filter_mock
        self.db_mock.query.return_value = query_mock
        
        # Get current user and expect exception
        with self.assertRaises(Exception):
            get_current_user("fake_token", self.db_mock)
    
    @patch('backend.security.security_system.decode_token')
    def test_get_current_user_token_error(self, mock_decode_token):
        """Test getting user with invalid token."""
        # Mock token decoding error
        mock_decode_token.side_effect = jwt.PyJWTError("Invalid token")
        
        # Get current user and expect exception
        with self.assertRaises(Exception):
            get_current_user("invalid_token", self.db_mock)


if __name__ == '__main__':
    unittest.main()
