import React, { useState, useEffect } from 'react';
import './Settings.css';

/**
 * Settings component for configuring application settings
 */
const Settings = () => {
  const [settings, setSettings] = useState({
    general: {
      theme: 'light',
      language: 'en',
      fontSize: 'medium',
      notifications: true
    },
    security: {
      twoFactorAuth: false,
      sessionTimeout: 30,
      ipRestriction: false,
      allowedIps: ''
    },
    api: {
      model: 'gpt-4',
      temperature: 0.7,
      maxTokens: 1000,
      apiKey: ''
    },
    advanced: {
      debugMode: false,
      logLevel: 'info',
      enableExperimental: false
    }
  });
  
  const [activeTab, setActiveTab] = useState('general');
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState(null);
  const [isApiKeyVisible, setIsApiKeyVisible] = useState(false);

  // Load settings on component mount
  useEffect(() => {
    fetchSettings();
  }, []);

  // Fetch settings from API
  const fetchSettings = async () => {
    try {
      const response = await fetch('/api/settings');
      const data = await response.json();
      
      if (data.success) {
        setSettings(data.settings);
      } else {
        console.error('Error fetching settings:', data.error);
      }
    } catch (error) {
      console.error('Error fetching settings:', error);
    }
  };

  // Save settings to API
  const saveSettings = async () => {
    setIsSaving(true);
    setSaveStatus(null);
    
    try {
      const response = await fetch('/api/settings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ settings })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setSaveStatus({ type: 'success', message: 'Settings saved successfully' });
      } else {
        setSaveStatus({ type: 'error', message: `Error saving settings: ${data.error}` });
      }
    } catch (error) {
      setSaveStatus({ type: 'error', message: `Error saving settings: ${error.message}` });
    } finally {
      setIsSaving(false);
      
      // Clear status after 3 seconds
      setTimeout(() => {
        setSaveStatus(null);
      }, 3000);
    }
  };

  // Handle input change
  const handleChange = (section, setting, value) => {
    setSettings(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [setting]: value
      }
    }));
  };

  // Reset settings to defaults
  const resetSettings = () => {
    if (window.confirm('Are you sure you want to reset all settings to defaults?')) {
      fetchSettings();
    }
  };

  // Render general settings tab
  const renderGeneralSettings = () => {
    return (
      <div className="settings-section">
        <h3>General Settings</h3>
        
        <div className="setting-group">
          <label>Theme</label>
          <select
            value={settings.general.theme}
            onChange={(e) => handleChange('general', 'theme', e.target.value)}
          >
            <option value="light">Light</option>
            <option value="dark">Dark</option>
            <option value="system">System Default</option>
          </select>
        </div>
        
        <div className="setting-group">
          <label>Language</label>
          <select
            value={settings.general.language}
            onChange={(e) => handleChange('general', 'language', e.target.value)}
          >
            <option value="en">English</option>
            <option value="ar">Arabic</option>
            <option value="fr">French</option>
            <option value="es">Spanish</option>
            <option value="de">German</option>
          </select>
        </div>
        
        <div className="setting-group">
          <label>Font Size</label>
          <select
            value={settings.general.fontSize}
            onChange={(e) => handleChange('general', 'fontSize', e.target.value)}
          >
            <option value="small">Small</option>
            <option value="medium">Medium</option>
            <option value="large">Large</option>
          </select>
        </div>
        
        <div className="setting-group checkbox">
          <label>
            <input
              type="checkbox"
              checked={settings.general.notifications}
              onChange={(e) => handleChange('general', 'notifications', e.target.checked)}
            />
            Enable Notifications
          </label>
        </div>
      </div>
    );
  };

  // Render security settings tab
  const renderSecuritySettings = () => {
    return (
      <div className="settings-section">
        <h3>Security Settings</h3>
        
        <div className="setting-group checkbox">
          <label>
            <input
              type="checkbox"
              checked={settings.security.twoFactorAuth}
              onChange={(e) => handleChange('security', 'twoFactorAuth', e.target.checked)}
            />
            Enable Two-Factor Authentication
          </label>
        </div>
        
        <div className="setting-group">
          <label>Session Timeout (minutes)</label>
          <input
            type="number"
            min="5"
            max="120"
            value={settings.security.sessionTimeout}
            onChange={(e) => handleChange('security', 'sessionTimeout', parseInt(e.target.value))}
          />
        </div>
        
        <div className="setting-group checkbox">
          <label>
            <input
              type="checkbox"
              checked={settings.security.ipRestriction}
              onChange={(e) => handleChange('security', 'ipRestriction', e.target.checked)}
            />
            Enable IP Restriction
          </label>
        </div>
        
        {settings.security.ipRestriction && (
          <div className="setting-group">
            <label>Allowed IP Addresses (comma-separated)</label>
            <input
              type="text"
              value={settings.security.allowedIps}
              onChange={(e) => handleChange('security', 'allowedIps', e.target.value)}
              placeholder="e.g., 192.168.1.1, 10.0.0.1"
            />
          </div>
        )}
      </div>
    );
  };

  // Render API settings tab
  const renderApiSettings = () => {
    return (
      <div className="settings-section">
        <h3>API Settings</h3>
        
        <div className="setting-group">
          <label>Language Model</label>
          <select
            value={settings.api.model}
            onChange={(e) => handleChange('api', 'model', e.target.value)}
          >
            <option value="gpt-4">GPT-4</option>
            <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
            <option value="claude-3">Claude 3</option>
            <option value="llama-3">Llama 3</option>
          </select>
        </div>
        
        <div className="setting-group">
          <label>Temperature (0.0 - 1.0)</label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={settings.api.temperature}
            onChange={(e) => handleChange('api', 'temperature', parseFloat(e.target.value))}
          />
          <span className="range-value">{settings.api.temperature}</span>
        </div>
        
        <div className="setting-group">
          <label>Max Tokens</label>
          <input
            type="number"
            min="100"
            max="8000"
            step="100"
            value={settings.api.maxTokens}
            onChange={(e) => handleChange('api', 'maxTokens', parseInt(e.target.value))}
          />
        </div>
        
        <div className="setting-group">
          <label>API Key</label>
          <div className="api-key-input">
            <input
              type={isApiKeyVisible ? "text" : "password"}
              value={settings.api.apiKey}
              onChange={(e) => handleChange('api', 'apiKey', e.target.value)}
              placeholder="Enter your API key"
            />
            <button
              type="button"
              className="toggle-visibility"
              onClick={() => setIsApiKeyVisible(!isApiKeyVisible)}
            >
              {isApiKeyVisible ? "Hide" : "Show"}
            </button>
          </div>
        </div>
      </div>
    );
  };

  // Render advanced settings tab
  const renderAdvancedSettings = () => {
    return (
      <div className="settings-section">
        <h3>Advanced Settings</h3>
        
        <div className="setting-group checkbox">
          <label>
            <input
              type="checkbox"
              checked={settings.advanced.debugMode}
              onChange={(e) => handleChange('advanced', 'debugMode', e.target.checked)}
            />
            Enable Debug Mode
          </label>
        </div>
        
        <div className="setting-group">
          <label>Log Level</label>
          <select
            value={settings.advanced.logLevel}
            onChange={(e) => handleChange('advanced', 'logLevel', e.target.value)}
          >
            <option value="error">Error</option>
            <option value="warn">Warning</option>
            <option value="info">Info</option>
            <option value="debug">Debug</option>
          </select>
        </div>
        
        <div className="setting-group checkbox">
          <label>
            <input
              type="checkbox"
              checked={settings.advanced.enableExperimental}
              onChange={(e) => handleChange('advanced', 'enableExperimental', e.target.checked)}
            />
            Enable Experimental Features
          </label>
        </div>
        
        <div className="danger-zone">
          <h4>Danger Zone</h4>
          <button
            type="button"
            className="danger-button"
            onClick={resetSettings}
          >
            Reset All Settings
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="settings-container">
      <div className="settings-header">
        <h2>Settings</h2>
        <button
          type="button"
          className="save-button"
          onClick={saveSettings}
          disabled={isSaving}
        >
          {isSaving ? 'Saving...' : 'Save Settings'}
        </button>
      </div>
      
      {saveStatus && (
        <div className={`save-status ${saveStatus.type}`}>
          {saveStatus.message}
        </div>
      )}
      
      <div className="settings-content">
        <div className="settings-tabs">
          <button
            className={`tab-button ${activeTab === 'general' ? 'active' : ''}`}
            onClick={() => setActiveTab('general')}
          >
            General
          </button>
          <button
            className={`tab-button ${activeTab === 'security' ? 'active' : ''}`}
            onClick={() => setActiveTab('security')}
          >
            Security
          </button>
          <button
            className={`tab-button ${activeTab === 'api' ? 'active' : ''}`}
            onClick={() => setActiveTab('api')}
          >
            API
          </button>
          <button
            className={`tab-button ${activeTab === 'advanced' ? 'active' : ''}`}
            onClick={() => setActiveTab('advanced')}
          >
            Advanced
          </button>
        </div>
        
        <div className="settings-panel">
          {activeTab === 'general' && renderGeneralSettings()}
          {activeTab === 'security' && renderSecuritySettings()}
          {activeTab === 'api' && renderApiSettings()}
          {activeTab === 'advanced' && renderAdvancedSettings()}
        </div>
      </div>
    </div>
  );
};

export default Settings;
