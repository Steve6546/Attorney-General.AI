"""
Attorney-General.AI - Chat Window Component

This component implements the main chat interface for the Attorney-General.AI frontend.
"""

import React, { useState, useEffect, useRef } from 'react';
import { useSession } from '../../../context/SessionContext';
import Message from './Message';
import InputArea from './InputArea';
import './ChatWindow.css';

const ChatWindow = () => {
  const { messages, loading, sendMessage, createNewSession } = useSession();
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (inputValue.trim() === '') return;
    
    sendMessage(inputValue);
    setInputValue('');
  };

  const handleInputChange = (e) => {
    setInputValue(e.target.value);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(e);
    }
  };

  const handleNewChat = () => {
    createNewSession();
  };

  return (
    <div className="chat-window">
      <div className="chat-header">
        <h2>المساعد القانوني</h2>
        <button className="new-chat-button" onClick={handleNewChat}>
          محادثة جديدة
        </button>
      </div>
      
      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="welcome-message">
            <h3>مرحباً بك في المساعد القانوني</h3>
            <p>يمكنك طرح أي سؤال قانوني وسأقوم بمساعدتك.</p>
          </div>
        ) : (
          messages.map((message) => (
            <Message 
              key={message.id} 
              content={message.content} 
              role={message.role} 
              timestamp={message.created_at}
            />
          ))
        )}
        
        {loading && (
          <div className="loading-indicator">
            <div className="loading-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      <InputArea 
        value={inputValue}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        onSubmit={handleSendMessage}
        disabled={loading}
      />
    </div>
  );
};

export default ChatWindow;
