"""
Attorney-General.AI - Frontend App Component

This is the main React component for the Attorney-General.AI frontend.
"""

import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

// Import components
import Header from './components/layout/Header';
import Sidebar from './components/layout/Sidebar';
import ChatWindow from './components/features/chat/ChatWindow';
import FileExplorer from './components/features/file-explorer/FileExplorer';
import LegalSearch from './components/features/legal-search/LegalSearch';
import Settings from './components/features/settings/Settings';

// Import styles
import './styles/App.css';

// Import context
import { SessionProvider } from './context/SessionContext';

function App() {
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  const [sidebarOpen, setSidebarOpen] = useState(!isMobile);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      if (mobile !== isMobile) {
        setSidebarOpen(!mobile);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [isMobile]);

  // Toggle sidebar
  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <SessionProvider>
      <Router>
        <div className="app-container">
          <Header toggleSidebar={toggleSidebar} />
          <div className="main-content">
            <Sidebar isOpen={sidebarOpen} isMobile={isMobile} closeSidebar={() => setSidebarOpen(false)} />
            <div className={`content-area ${sidebarOpen ? 'sidebar-open' : ''}`}>
              <Routes>
                <Route path="/" element={<ChatWindow />} />
                <Route path="/files" element={<FileExplorer />} />
                <Route path="/search" element={<LegalSearch />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </div>
          </div>
        </div>
      </Router>
    </SessionProvider>
  );
}

export default App;
