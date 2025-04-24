"""
Attorney-General.AI - Sidebar Component

This component implements the sidebar navigation for the application.
"""

import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Sidebar.css';

const Sidebar = ({ isOpen, isMobile, closeSidebar }) => {
  const location = useLocation();
  
  // Close sidebar on mobile when clicking a link
  const handleLinkClick = () => {
    if (isMobile) {
      closeSidebar();
    }
  };
  
  // Check if a route is active
  const isActive = (path) => {
    return location.pathname === path;
  };
  
  return (
    <div className={`sidebar ${isOpen ? 'open' : 'closed'}`}>
      <div className="sidebar-header">
        <h2>القائمة</h2>
        {isMobile && (
          <button className="close-sidebar" onClick={closeSidebar}>
            ×
          </button>
        )}
      </div>
      
      <nav className="sidebar-nav">
        <ul>
          <li className={isActive('/') ? 'active' : ''}>
            <Link to="/" onClick={handleLinkClick}>
              <span className="nav-icon">💬</span>
              <span className="nav-text">المحادثة</span>
            </Link>
          </li>
          <li className={isActive('/files') ? 'active' : ''}>
            <Link to="/files" onClick={handleLinkClick}>
              <span className="nav-icon">📁</span>
              <span className="nav-text">الملفات</span>
            </Link>
          </li>
          <li className={isActive('/search') ? 'active' : ''}>
            <Link to="/search" onClick={handleLinkClick}>
              <span className="nav-icon">🔍</span>
              <span className="nav-text">البحث القانوني</span>
            </Link>
          </li>
          <li className={isActive('/settings') ? 'active' : ''}>
            <Link to="/settings" onClick={handleLinkClick}>
              <span className="nav-icon">⚙️</span>
              <span className="nav-text">الإعدادات</span>
            </Link>
          </li>
        </ul>
      </nav>
      
      <div className="sidebar-footer">
        <div className="version-info">
          الإصدار 2.0.0
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
