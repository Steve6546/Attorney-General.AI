import React, { useState, useEffect } from 'react';
import './FileExplorer.css';

/**
 * FileExplorer component for browsing and managing legal documents
 */
const FileExplorer = () => {
  const [files, setFiles] = useState([]);
  const [folders, setFolders] = useState([]);
  const [currentPath, setCurrentPath] = useState('/');
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredItems, setFilteredItems] = useState({ files: [], folders: [] });
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'list'
  const [sortBy, setSortBy] = useState('name'); // 'name', 'date', 'size'
  const [sortDirection, setSortDirection] = useState('asc'); // 'asc' or 'desc'

  // Fetch files and folders on component mount and when path changes
  useEffect(() => {
    fetchFilesAndFolders(currentPath);
  }, [currentPath]);

  // Filter items when search query changes
  useEffect(() => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      setFilteredItems({
        files: files.filter(file => file.name.toLowerCase().includes(query)),
        folders: folders.filter(folder => folder.name.toLowerCase().includes(query))
      });
    } else {
      setFilteredItems({ files, folders });
    }
  }, [searchQuery, files, folders]);

  // Sort items when sort parameters change
  useEffect(() => {
    const sortedFiles = [...files];
    const sortedFolders = [...folders];
    
    const compareFn = (a, b) => {
      let comparison = 0;
      
      if (sortBy === 'name') {
        comparison = a.name.localeCompare(b.name);
      } else if (sortBy === 'date') {
        comparison = new Date(a.modified) - new Date(b.modified);
      } else if (sortBy === 'size' && 'size' in a && 'size' in b) {
        comparison = a.size - b.size;
      }
      
      return sortDirection === 'asc' ? comparison : -comparison;
    };
    
    sortedFiles.sort(compareFn);
    sortedFolders.sort(compareFn);
    
    setFiles(sortedFiles);
    setFolders(sortedFolders);
  }, [sortBy, sortDirection]);

  // Fetch files and folders from API
  const fetchFilesAndFolders = async (path) => {
    try {
      const response = await fetch(`/api/files?path=${encodeURIComponent(path)}`);
      const data = await response.json();
      
      if (data.success) {
        setFiles(data.files || []);
        setFolders(data.folders || []);
      } else {
        console.error('Error fetching files:', data.error);
      }
    } catch (error) {
      console.error('Error fetching files:', error);
    }
  };

  // Handle file selection
  const handleFileSelect = (file) => {
    setSelectedFile(file);
  };

  // Handle folder navigation
  const handleFolderClick = (folder) => {
    setCurrentPath(`${currentPath}${folder.name}/`);
  };

  // Handle navigation to parent folder
  const handleNavigateUp = () => {
    if (currentPath === '/') return;
    
    const pathParts = currentPath.split('/').filter(Boolean);
    pathParts.pop();
    const newPath = pathParts.length ? `/${pathParts.join('/')}/` : '/';
    
    setCurrentPath(newPath);
  };

  // Handle file upload
  const handleFileUpload = async (event) => {
    const files = event.target.files;
    if (!files.length) return;
    
    setIsUploading(true);
    
    try {
      const formData = new FormData();
      formData.append('path', currentPath);
      
      for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
      }
      
      const response = await fetch('/api/files/upload', {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      
      if (data.success) {
        fetchFilesAndFolders(currentPath);
      } else {
        console.error('Error uploading files:', data.error);
      }
    } catch (error) {
      console.error('Error uploading files:', error);
    } finally {
      setIsUploading(false);
    }
  };

  // Handle file deletion
  const handleDeleteFile = async (file) => {
    if (!window.confirm(`Are you sure you want to delete ${file.name}?`)) {
      return;
    }
    
    try {
      const response = await fetch(`/api/files?path=${encodeURIComponent(currentPath + file.name)}`, {
        method: 'DELETE'
      });
      
      const data = await response.json();
      
      if (data.success) {
        if (selectedFile && selectedFile.name === file.name) {
          setSelectedFile(null);
        }
        fetchFilesAndFolders(currentPath);
      } else {
        console.error('Error deleting file:', data.error);
      }
    } catch (error) {
      console.error('Error deleting file:', error);
    }
  };

  // Handle folder creation
  const handleCreateFolder = async () => {
    const folderName = prompt('Enter folder name:');
    if (!folderName) return;
    
    try {
      const response = await fetch('/api/folders', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          path: currentPath,
          name: folderName
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        fetchFilesAndFolders(currentPath);
      } else {
        console.error('Error creating folder:', data.error);
      }
    } catch (error) {
      console.error('Error creating folder:', error);
    }
  };

  // Handle search query change
  const handleSearchChange = (event) => {
    setSearchQuery(event.target.value);
  };

  // Handle sort change
  const handleSortChange = (newSortBy) => {
    if (sortBy === newSortBy) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(newSortBy);
      setSortDirection('asc');
    }
  };

  // Format file size
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Format date
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  // Render breadcrumb navigation
  const renderBreadcrumbs = () => {
    const pathParts = currentPath.split('/').filter(Boolean);
    
    return (
      <div className="breadcrumbs">
        <span 
          className="breadcrumb-item home"
          onClick={() => setCurrentPath('/')}
        >
          Home
        </span>
        
        {pathParts.map((part, index) => (
          <span key={index}>
            <span className="breadcrumb-separator">/</span>
            <span 
              className="breadcrumb-item"
              onClick={() => {
                const newPath = '/' + pathParts.slice(0, index + 1).join('/') + '/';
                setCurrentPath(newPath);
              }}
            >
              {part}
            </span>
          </span>
        ))}
      </div>
    );
  };

  return (
    <div className="file-explorer">
      <div className="file-explorer-header">
        <h2>Document Explorer</h2>
        
        <div className="file-explorer-actions">
          <div className="search-container">
            <input
              type="text"
              placeholder="Search files..."
              value={searchQuery}
              onChange={handleSearchChange}
              className="search-input"
            />
          </div>
          
          <div className="view-options">
            <button
              className={`view-option ${viewMode === 'grid' ? 'active' : ''}`}
              onClick={() => setViewMode('grid')}
              title="Grid view"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="7" height="7"></rect>
                <rect x="14" y="3" width="7" height="7"></rect>
                <rect x="14" y="14" width="7" height="7"></rect>
                <rect x="3" y="14" width="7" height="7"></rect>
              </svg>
            </button>
            
            <button
              className={`view-option ${viewMode === 'list' ? 'active' : ''}`}
              onClick={() => setViewMode('list')}
              title="List view"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="8" y1="6" x2="21" y2="6"></line>
                <line x1="8" y1="12" x2="21" y2="12"></line>
                <line x1="8" y1="18" x2="21" y2="18"></line>
                <line x1="3" y1="6" x2="3.01" y2="6"></line>
                <line x1="3" y1="12" x2="3.01" y2="12"></line>
                <line x1="3" y1="18" x2="3.01" y2="18"></line>
              </svg>
            </button>
          </div>
          
          <button 
            className="action-button"
            onClick={handleCreateFolder}
            title="Create folder"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
              <line x1="12" y1="11" x2="12" y2="17"></line>
              <line x1="9" y1="14" x2="15" y2="14"></line>
            </svg>
          </button>
          
          <label className="action-button upload-button" title="Upload files">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
            <input 
              type="file" 
              multiple 
              onChange={handleFileUpload} 
              style={{ display: 'none' }} 
            />
          </label>
        </div>
      </div>
      
      <div className="file-explorer-navigation">
        {renderBreadcrumbs()}
        
        <button 
          className="nav-button"
          onClick={handleNavigateUp}
          disabled={currentPath === '/'}
          title="Go up"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
            <polyline points="9 22 9 12 15 12 15 22"></polyline>
          </svg>
        </button>
      </div>
      
      {isUploading && (
        <div className="upload-progress">
          <div className="spinner"></div>
          <span>Uploading files...</span>
        </div>
      )}
      
      {viewMode === 'list' ? (
        <div className="file-list-view">
          <table className="file-table">
            <thead>
              <tr>
                <th 
                  className={`sortable ${sortBy === 'name' ? 'sorted-' + sortDirection : ''}`}
                  onClick={() => handleSortChange('name')}
                >
                  Name
                  {sortBy === 'name' && (
                    <span className="sort-indicator">
                      {sortDirection === 'asc' ? '↑' : '↓'}
                    </span>
                  )}
                </th>
                <th 
                  className={`sortable ${sortBy === 'date' ? 'sorted-' + sortDirection : ''}`}
                  onClick={() => handleSortChange('date')}
                >
                  Modified
                  {sortBy === 'date' && (
                    <span className="sort-indicator">
                      {sortDirection === 'asc' ? '↑' : '↓'}
                    </span>
                  )}
                </th>
                <th 
                  className={`sortable ${sortBy === 'size' ? 'sorted-' + sortDirection : ''}`}
                  onClick={() => handleSortChange('size')}
                >
                  Size
                  {sortBy === 'size' && (
                    <span className="sort-indicator">
                      {sortDirection === 'asc' ? '↑' : '↓'}
                    </span>
                  )}
                </th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredItems.folders.map((folder) => (
                <tr 
                  key={folder.name}
                  className="folder-row"
                  onDoubleClick={() => handleFolderClick(folder)}
                >
                  <td className="name-cell">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                    </svg>
                    {folder.name}
                  </td>
                  <td>{formatDate(folder.modified)}</td>
                  <td>-</td>
                  <td className="actions-cell">
                    <button 
                      className="action-button small"
                      onClick={() => handleFolderClick(folder)}
                      title="Open folder"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                        <polyline points="15 3 21 3 21 9"></polyline>
                        <line x1="10" y1="14" x2="21" y2="3"></line>
                      </svg>
                    </button>
                  </td>
                </tr>
              ))}
              
              {filteredItems.files.map((file) => (
                <tr 
                  key={file.name}
                  className={`file-row ${selectedFile && selectedFile.name === file.name ? 'selected' : ''}`}
                  onClick={() => handleFileSelect(file)}
                >
                  <td className="name-cell">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                      <polyline points="14 2 14 8 20 8"></polyline>
                      <line x1="16" y1="13" x2="8" y2="13"></line>
                      <line x1="16" y1="17" x2="8" y2="17"></line>
                      <polyline points="10 9 9 9 8 9"></polyline>
                    </svg>
                    {file.name}
                  </td>
                  <td>{formatDate(file.modified)}</td>
                  <td>{formatFileSize(file.size)}</td>
                  <td className="actions-cell">
                    <button 
                      className="action-button small"
                      onClick={(e) => {
                        e.stopPropagation();
                        window.open(`/api/files/download?path=${encodeURIComponent(currentPath + file.name)}`, '_blank');
                      }}
                      title="Download file"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="7 10 12 15 17 10"></polyline>
                        <line x1="12" y1="15" x2="12" y2="3"></line>
                      </svg>
                    </button>
                    <button 
                      className="action-button small delete"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteFile(file);
                      }}
                      title="Delete file"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                      </svg>
                    </button>
                  </td>
                </tr>
              ))}
              
              {filteredItems.folders.length === 0 && filteredItems.files.length === 0 && (
                <tr>
                  <td colSpan="4" className="empty-message">
                    {searchQuery ? 'No files or folders match your search.' : 'This folder is empty.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="file-grid-view">
          {filteredItems.folders.map((folder) => (
            <div 
              key={folder.name}
              className="grid-item folder"
              onDoubleClick={() => handleFolderClick(folder)}
            >
              <div className="grid-item-icon">
                <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                </svg>
              </div>
              <div className="grid-item-name">{folder.name}</div>
            </div>
          ))}
          
          {filteredItems.files.map((file) => (
            <div 
              key={file.name}
              className={`grid-item file ${selectedFile && selectedFile.name === file.name ? 'selected' : ''}`}
              onClick={() => handleFileSelect(file)}
            >
              <div className="grid-item-icon">
                <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                  <line x1="16" y1="13" x2="8" y2="13"></line>
                  <line x1="16" y1="17" x2="8" y2="17"></line>
                  <polyline points="10 9 9 9 8 9"></polyline>
                </svg>
              </div>
              <div className="grid-item-name">{file.name}</div>
              <div className="grid-item-actions">
                <button 
                  className="action-button small"
                  onClick={(e) => {
                    e.stopPropagation();
                    window.open(`/api/files/download?path=${encodeURIComponent(currentPath + file.name)}`, '_blank');
                  }}
                  title="Download file"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="7 10 12 15 17 10"></polyline>
                    <line x1="12" y1="15" x2="12" y2="3"></line>
                  </svg>
                </button>
                <button 
                  className="action-button small delete"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteFile(file);
                  }}
                  title="Delete file"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                  </svg>
                </button>
              </div>
            </div>
          ))}
          
          {filteredItems.folders.length === 0 && filteredItems.files.length === 0 && (
            <div className="empty-message">
              {searchQuery ? 'No files or folders match your search.' : 'This folder is empty.'}
            </div>
          )}
        </div>
      )}
      
      {selectedFile && (
        <div className="file-preview">
          <h3>File Preview: {selectedFile.name}</h3>
          <div className="file-info">
            <div><strong>Size:</strong> {formatFileSize(selectedFile.size)}</div>
            <div><strong>Modified:</strong> {formatDate(selectedFile.modified)}</div>
            <div><strong>Type:</strong> {selectedFile.type || 'Unknown'}</div>
          </div>
          <div className="preview-actions">
            <button 
              className="action-button"
              onClick={() => window.open(`/api/files/download?path=${encodeURIComponent(currentPath + selectedFile.name)}`, '_blank')}
            >
              Download
            </button>
            <button 
              className="action-button"
              onClick={() => window.open(`/api/files/view?path=${encodeURIComponent(currentPath + selectedFile.name)}`, '_blank')}
            >
              View
            </button>
            <button 
              className="action-button delete"
              onClick={() => handleDeleteFile(selectedFile)}
            >
              Delete
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileExplorer;
