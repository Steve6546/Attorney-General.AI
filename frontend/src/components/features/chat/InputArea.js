"""
Attorney-General.AI - Input Area Component

This component implements the input area for the chat interface.
"""

import React from 'react';
import './InputArea.css';

const InputArea = ({ value, onChange, onKeyDown, onSubmit, disabled }) => {
  return (
    <div className="input-area">
      <form onSubmit={onSubmit}>
        <div className="input-container">
          <textarea
            className="message-input"
            value={value}
            onChange={onChange}
            onKeyDown={onKeyDown}
            placeholder="اكتب سؤالك القانوني هنا..."
            disabled={disabled}
            rows={1}
          />
          <button 
            type="submit" 
            className="send-button"
            disabled={disabled || !value.trim()}
          >
            إرسال
          </button>
        </div>
        <div className="input-footer">
          <span className="disclaimer">
            هذا المساعد يقدم معلومات عامة فقط وليس بديلاً عن المشورة القانونية المتخصصة.
          </span>
        </div>
      </form>
    </div>
  );
};

export default InputArea;
