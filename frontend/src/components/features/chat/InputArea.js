import React, { useState, useRef } from 'react';
import './InputArea.css';

/**
 * InputArea component for chat message input
 */
const InputArea = ({ value, onChange, onKeyPress, onSend, disabled = false }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const textareaRef = useRef(null);
  
  // Auto-resize textarea based on content
  const handleInput = (e) => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    
    // Reset height to auto to get the correct scrollHeight
    textarea.style.height = 'auto';
    
    // Set new height based on scrollHeight (with max height)
    const newHeight = Math.min(textarea.scrollHeight, 200);
    textarea.style.height = `${newHeight}px`;
    
    // Update expanded state
    setIsExpanded(newHeight > 50);
    
    // Call parent onChange handler
    onChange(e);
  };
  
  return (
    <div className={`input-area ${isExpanded ? 'expanded' : ''}`}>
      <textarea
        ref={textareaRef}
        className="message-input"
        value={value}
        onChange={onChange}
        onInput={handleInput}
        onKeyPress={onKeyPress}
        placeholder="Type your message here..."
        disabled={disabled}
        rows={1}
      />
      
      <button 
        className="send-button"
        onClick={onSend}
        disabled={disabled || !value.trim()}
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <line x1="22" y1="2" x2="11" y2="13"></line>
          <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
        </svg>
      </button>
      
      <div className="input-actions">
        <button className="action-button upload-button" title="Upload file">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="17 8 12 3 7 8"></polyline>
            <line x1="12" y1="3" x2="12" y2="15"></line>
          </svg>
        </button>
        
        <button className="action-button mic-button" title="Voice input">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
            <line x1="12" y1="19" x2="12" y2="23"></line>
            <line x1="8" y1="23" x2="16" y2="23"></line>
          </svg>
        </button>
      </div>
      
      {isExpanded && (
        <div className="formatting-toolbar">
          <button className="format-button" title="Bold">
            <strong>B</strong>
          </button>
          <button className="format-button" title="Italic">
            <em>I</em>
          </button>
          <button className="format-button" title="Code">
            <code>{`<>`}</code>
          </button>
          <button className="format-button" title="Link">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
              <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
            </svg>
          </button>
        </div>
      )}
    </div>
  );
};

export default InputArea;
