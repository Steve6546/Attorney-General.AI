import React, { useState, useEffect, useRef } from 'react';
import { useSession } from '../../context/SessionContext';
import Message from './Message';
import InputArea from './InputArea';
import './ChatWindow.css';

/**
 * ChatWindow component for displaying and managing chat messages
 */
const ChatWindow = () => {
  const { currentSession, messages, sendMessage, loadingMessage } = useSession();
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Handle sending a message
  const handleSendMessage = async () => {
    if (inputValue.trim() === '') return;
    
    const userMessage = inputValue;
    setInputValue('');
    
    await sendMessage(userMessage);
  };

  // Handle input change
  const handleInputChange = (e) => {
    setInputValue(e.target.value);
  };

  // Handle key press (Enter to send)
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="chat-window">
      <div className="chat-header">
        <h2>{currentSession?.title || 'New Conversation'}</h2>
      </div>
      
      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="empty-chat">
            <h3>Welcome to Attorney General AI</h3>
            <p>Start a conversation by typing a message below.</p>
          </div>
        ) : (
          messages.map((message) => (
            <Message 
              key={message.id} 
              role={message.role} 
              content={message.content} 
              timestamp={message.created_at}
            />
          ))
        )}
        
        {loadingMessage && (
          <Message 
            role="assistant" 
            content="Thinking..." 
            isLoading={true} 
          />
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      <InputArea 
        value={inputValue}
        onChange={handleInputChange}
        onKeyPress={handleKeyPress}
        onSend={handleSendMessage}
        disabled={loadingMessage || !currentSession}
      />
    </div>
  );
};

export default ChatWindow;
