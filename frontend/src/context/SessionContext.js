"""
Attorney-General.AI - Session Context Provider

This component provides session context for the Attorney-General.AI frontend.
"""

import React, { createContext, useState, useContext, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';

// Create context
const SessionContext = createContext();

// Custom hook to use the session context
export const useSession = () => useContext(SessionContext);

// Session provider component
export const SessionProvider = ({ children }) => {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Initialize session on component mount
  useEffect(() => {
    // Check for existing session in localStorage
    const storedSessionId = localStorage.getItem('sessionId');
    
    if (storedSessionId) {
      setSessionId(storedSessionId);
      // Load messages for this session
      fetchMessages(storedSessionId);
    } else {
      // Create new session
      const newSessionId = uuidv4();
      setSessionId(newSessionId);
      localStorage.setItem('sessionId', newSessionId);
    }
  }, []);

  // Fetch messages for a session
  const fetchMessages = async (sid) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/history/${sid}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch messages');
      }
      
      const data = await response.json();
      setMessages(data.messages || []);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching messages:', err);
    } finally {
      setLoading(false);
    }
  };

  // Send a message
  const sendMessage = async (content) => {
    try {
      setLoading(true);
      
      // Add user message to state immediately for UI responsiveness
      const userMessage = {
        id: uuidv4(),
        content,
        role: 'user',
        created_at: new Date().toISOString()
      };
      
      setMessages(prevMessages => [...prevMessages, userMessage]);
      
      // Send to API
      const response = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content,
          session_id: sessionId
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to send message');
      }
      
      const data = await response.json();
      
      // Add assistant response to state
      const assistantMessage = {
        id: data.message_id,
        content: data.content,
        role: 'assistant',
        created_at: new Date().toISOString()
      };
      
      setMessages(prevMessages => [...prevMessages, assistantMessage]);
      
    } catch (err) {
      setError(err.message);
      console.error('Error sending message:', err);
      
      // Add error message to chat
      const errorMessage = {
        id: uuidv4(),
        content: 'Sorry, there was an error processing your request. Please try again.',
        role: 'system',
        created_at: new Date().toISOString()
      };
      
      setMessages(prevMessages => [...prevMessages, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  // Create a new session
  const createNewSession = () => {
    const newSessionId = uuidv4();
    setSessionId(newSessionId);
    setMessages([]);
    localStorage.setItem('sessionId', newSessionId);
  };

  // Context value
  const value = {
    sessionId,
    messages,
    loading,
    error,
    sendMessage,
    createNewSession
  };

  return (
    <SessionContext.Provider value={value}>
      {children}
    </SessionContext.Provider>
  );
};

export default SessionContext;
