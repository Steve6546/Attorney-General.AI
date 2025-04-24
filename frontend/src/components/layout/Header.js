"""
Attorney-General.AI - Header Component

This component implements the header for the application.
"""

import React from 'react';
import './Header.css';

const Header = ({ toggleSidebar }) => {
  return (
    <header className="app-header">
      <div className="header-left">
        <button className="menu-button" onClick={toggleSidebar}>
          <span className="menu-icon">☰</span>
        </button>
        <h1 className="app-title">Attorney-General.AI</h1>
      </div>
      <div className="header-right">
        <div className="user-info">
          <span className="user-name">مستخدم</span>
          <div className="user-avatar">👤</div>
        </div>
      </div>
    </header>
  );
};

export default Header;
