"""
Attorney-General.AI - File Explorer Component

This component implements the file explorer interface for document management.
"""

import React, { useState, useEffect } from 'react';
import './FileExplorer.css';

const FileExplorer = () => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);

  // Fetch files on component mount
  useEffect(() => {
    fetchFiles();
  }, []);

  // Fetch files from API
  const fetchFiles = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/documents');
      
      if (!response.ok) {
        throw new Error('Failed to fetch documents');
      }
      
      const data = await response.json();
      setFiles(data.documents || []);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching documents:', err);
    } finally {
      setLoading(false);
    }
  };

  // Handle file selection
  const handleFileSelect = (file) => {
    setSelectedFile(file);
  };

  // Handle file upload
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    try {
      setIsUploading(true);
      setUploadProgress(0);
      
      const formData = new FormData();
      formData.append('file', file);
      
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 300);
      
      const response = await fetch('/api/v1/upload_document', {
        method: 'POST',
        body: formData,
      });
      
      clearInterval(progressInterval);
      
      if (!response.ok) {
        throw new Error('Failed to upload document');
      }
      
      setUploadProgress(100);
      
      // Add small delay to show 100% before resetting
      setTimeout(() => {
        setIsUploading(false);
        setUploadProgress(0);
        fetchFiles(); // Refresh file list
      }, 500);
      
    } catch (err) {
      setError(err.message);
      console.error('Error uploading document:', err);
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  return (
    <div className="file-explorer">
      <div className="file-explorer-header">
        <h2>مستكشف الملفات</h2>
        <div className="upload-container">
          <label className="upload-button">
            تحميل ملف
            <input 
              type="file" 
              onChange={handleFileUpload} 
              style={{ display: 'none' }}
              accept=".pdf,.doc,.docx,.txt"
              disabled={isUploading}
            />
          </label>
          {isUploading && (
            <div className="upload-progress">
              <div 
                className="progress-bar" 
                style={{ width: `${uploadProgress}%` }}
              ></div>
              <span className="progress-text">{uploadProgress}%</span>
            </div>
          )}
        </div>
      </div>
      
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}
      
      <div className="files-container">
        {loading ? (
          <div className="loading-indicator">جاري تحميل الملفات...</div>
        ) : files.length === 0 ? (
          <div className="empty-state">
            <p>لا توجد ملفات حالياً</p>
            <p>قم بتحميل ملف للبدء</p>
          </div>
        ) : (
          <div className="file-list">
            {files.map(file => (
              <div 
                key={file.id} 
                className={`file-item ${selectedFile?.id === file.id ? 'selected' : ''}`}
                onClick={() => handleFileSelect(file)}
              >
                <div className="file-icon">📄</div>
                <div className="file-details">
                  <div className="file-name">{file.filename}</div>
                  <div className="file-meta">
                    <span className="file-date">
                      {new Date(file.uploaded_at).toLocaleDateString()}
                    </span>
                    <span className="file-size">
                      {Math.round(file.size / 1024)} KB
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {selectedFile && (
        <div className="file-preview">
          <h3>معلومات الملف</h3>
          <div className="file-info">
            <p><strong>اسم الملف:</strong> {selectedFile.filename}</p>
            <p><strong>تاريخ التحميل:</strong> {new Date(selectedFile.uploaded_at).toLocaleString()}</p>
            <p><strong>الحجم:</strong> {Math.round(selectedFile.size / 1024)} KB</p>
            <p><strong>نوع الملف:</strong> {selectedFile.content_type}</p>
          </div>
          <div className="file-actions">
            <button className="action-button">عرض</button>
            <button className="action-button">تحليل</button>
            <button className="action-button danger">حذف</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileExplorer;
