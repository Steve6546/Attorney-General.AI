import React, { useState, useEffect } from 'react';
import { useSession } from '../../context/SessionContext';
import './Message.css';

/**
 * Message component for displaying a single chat message
 */
const Message = ({ role, content, timestamp, isLoading = false }) => {
  const [formattedContent, setFormattedContent] = useState('');
  const [showTimestamp, setShowTimestamp] = useState(false);
  
  // Format message content with markdown and code highlighting
  useEffect(() => {
    if (isLoading) {
      setFormattedContent('<div class="typing-indicator"><span></span><span></span><span></span></div>');
      return;
    }
    
    // Process content for display (handle markdown, code blocks, etc.)
    const processedContent = processMessageContent(content);
    setFormattedContent(processedContent);
  }, [content, isLoading]);
  
  // Format timestamp
  const formatTimestamp = (timestamp) => {
    if (!timestamp) return '';
    
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };
  
  // Process message content to handle markdown, code blocks, etc.
  const processMessageContent = (content) => {
    if (!content) return '';
    
    // Replace code blocks
    let processed = content.replace(/```([a-z]*)\n([\s\S]*?)```/g, (match, language, code) => {
      return `<pre class="code-block ${language}"><code>${escapeHtml(code)}</code></pre>`;
    });
    
    // Replace inline code
    processed = processed.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
    
    // Replace bold text
    processed = processed.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    
    // Replace italic text
    processed = processed.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    
    // Replace links
    processed = processed.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
    
    // Replace newlines with <br>
    processed = processed.replace(/\n/g, '<br>');
    
    return processed;
  };
  
  // Escape HTML special characters
  const escapeHtml = (unsafe) => {
    return unsafe
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  };
  
  return (
    <div 
      className={`message ${role === 'user' ? 'user-message' : 'assistant-message'}`}
      onMouseEnter={() => setShowTimestamp(true)}
      onMouseLeave={() => setShowTimestamp(false)}
    >
      <div className="message-avatar">
        {role === 'user' ? (
          <div className="user-avatar">U</div>
        ) : (
          <div className="assistant-avatar">AI</div>
        )}
      </div>
      
      <div className="message-content">
        <div 
          className="message-text"
          dangerouslySetInnerHTML={{ __html: formattedContent }}
        />
        
        {showTimestamp && timestamp && (
          <div className="message-timestamp">
            {formatTimestamp(timestamp)}
          </div>
        )}
      </div>
    </div>
  );
};

export default Message;
