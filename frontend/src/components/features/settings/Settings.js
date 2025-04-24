"""
Attorney-General.AI - Settings Component

This component implements the settings interface for the application.
"""

import React, { useState, useEffect } from 'react';
import './Settings.css';

const Settings = () => {
  const [settings, setSettings] = useState({
    language: 'ar',
    theme: 'light',
    fontSize: 'medium',
    notifications: true,
    saveHistory: true
  });
  
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(false);
  
  // Handle settings change
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setSettings(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    
    // Reset saved status when settings change
    setSaved(false);
  };
  
  // Handle settings save
  const handleSave = async (e) => {
    e.preventDefault();
    
    try {
      setLoading(true);
      
      // Simulate API call to save settings
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Save settings to localStorage
      localStorage.setItem('settings', JSON.stringify(settings));
      
      setSaved(true);
      
      // Reset saved status after 3 seconds
      setTimeout(() => {
        setSaved(false);
      }, 3000);
      
    } catch (err) {
      console.error('Error saving settings:', err);
    } finally {
      setLoading(false);
    }
  };
  
  // Load settings from localStorage on component mount
  useEffect(() => {
    const savedSettings = localStorage.getItem('settings');
    if (savedSettings) {
      setSettings(JSON.parse(savedSettings));
    }
  }, []);
  
  return (
    <div className="settings">
      <div className="settings-header">
        <h2>الإعدادات</h2>
      </div>
      
      <form onSubmit={handleSave} className="settings-form">
        <div className="settings-section">
          <h3>إعدادات الواجهة</h3>
          
          <div className="setting-item">
            <label htmlFor="language">اللغة:</label>
            <select 
              id="language" 
              name="language" 
              value={settings.language} 
              onChange={handleChange}
            >
              <option value="ar">العربية</option>
              <option value="en">English</option>
            </select>
          </div>
          
          <div className="setting-item">
            <label htmlFor="theme">المظهر:</label>
            <select 
              id="theme" 
              name="theme" 
              value={settings.theme} 
              onChange={handleChange}
            >
              <option value="light">فاتح</option>
              <option value="dark">داكن</option>
              <option value="system">تلقائي (حسب النظام)</option>
            </select>
          </div>
          
          <div className="setting-item">
            <label htmlFor="fontSize">حجم الخط:</label>
            <select 
              id="fontSize" 
              name="fontSize" 
              value={settings.fontSize} 
              onChange={handleChange}
            >
              <option value="small">صغير</option>
              <option value="medium">متوسط</option>
              <option value="large">كبير</option>
            </select>
          </div>
        </div>
        
        <div className="settings-section">
          <h3>إعدادات الخصوصية</h3>
          
          <div className="setting-item checkbox">
            <label htmlFor="notifications">
              <input 
                type="checkbox" 
                id="notifications" 
                name="notifications" 
                checked={settings.notifications} 
                onChange={handleChange}
              />
              تفعيل الإشعارات
            </label>
          </div>
          
          <div className="setting-item checkbox">
            <label htmlFor="saveHistory">
              <input 
                type="checkbox" 
                id="saveHistory" 
                name="saveHistory" 
                checked={settings.saveHistory} 
                onChange={handleChange}
              />
              حفظ سجل المحادثات
            </label>
          </div>
        </div>
        
        <div className="settings-actions">
          <button 
            type="submit" 
            className="save-button"
            disabled={loading}
          >
            {loading ? 'جاري الحفظ...' : 'حفظ الإعدادات'}
          </button>
          
          {saved && (
            <div className="save-confirmation">
              تم حفظ الإعدادات بنجاح!
            </div>
          )}
        </div>
      </form>
      
      <div className="settings-section">
        <h3>معلومات النظام</h3>
        <div className="system-info">
          <p><strong>إصدار التطبيق:</strong> 2.0.0</p>
          <p><strong>آخر تحديث:</strong> {new Date().toLocaleDateString()}</p>
        </div>
      </div>
    </div>
  );
};

export default Settings;
