"""
Attorney-General.AI - Message Component

This component renders a single message in the chat interface.
"""

import React from 'react';
import './Message.css';

const Message = ({ content, role, timestamp }) => {
  // Format timestamp
  const formatTimestamp = (timestamp) => {
    if (!timestamp) return '';
    
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Determine message class based on role
  const getMessageClass = () => {
    switch (role) {
      case 'user':
        return 'user-message';
      case 'assistant':
        return 'assistant-message';
      case 'system':
        return 'system-message';
      default:
        return 'assistant-message';
    }
  };

  // Determine avatar based on role
  const getAvatar = () => {
    switch (role) {
      case 'user':
        return '👤';
      case 'assistant':
        return '⚖️';
      case 'system':
        return '🔔';
      default:
        return '⚖️';
    }
  };

  return (
    <div className={`message ${getMessageClass()}`}>
      <div className="message-avatar">
        {getAvatar()}
      </div>
      <div className="message-content">
        <div className="message-header">
          <span className="message-role">
            {role === 'user' ? 'أنت' : role === 'assistant' ? 'المساعد القانوني' : 'النظام'}
          </span>
          <span className="message-timestamp">{formatTimestamp(timestamp)}</span>
        </div>
        <div className="message-text">
          {content}
        </div>
      </div>
    </div>
  );
};

export default Message;
