import React, { useState, useEffect } from 'react';
import './LegalSearch.css';

/**
 * LegalSearch component for searching legal resources
 */
const LegalSearch = () => {
  const [query, setQuery] = useState('');
  const [jurisdiction, setJurisdiction] = useState('US');
  const [searchType, setSearchType] = useState('all');
  const [dateRange, setDateRange] = useState('all');
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState([]);
  const [selectedResult, setSelectedResult] = useState(null);
  const [searchHistory, setSearchHistory] = useState([]);
  const [filters, setFilters] = useState({
    courts: [],
    docTypes: [],
    years: []
  });
  const [appliedFilters, setAppliedFilters] = useState({
    courts: [],
    docTypes: [],
    years: []
  });

  // Load search history from local storage on component mount
  useEffect(() => {
    const savedHistory = localStorage.getItem('legalSearchHistory');
    if (savedHistory) {
      try {
        setSearchHistory(JSON.parse(savedHistory));
      } catch (error) {
        console.error('Error loading search history:', error);
      }
    }
  }, []);

  // Save search history to local storage when it changes
  useEffect(() => {
    localStorage.setItem('legalSearchHistory', JSON.stringify(searchHistory));
  }, [searchHistory]);

  // Handle search submission
  const handleSearch = async (e) => {
    e?.preventDefault();
    
    if (!query.trim()) return;
    
    setIsSearching(true);
    setResults([]);
    setSelectedResult(null);
    
    try {
      const response = await fetch('/api/legal-search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          query,
          jurisdiction,
          type: searchType,
          dateRange,
          filters: appliedFilters
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setResults(data.results || []);
        
        // Extract available filters from results
        const courts = new Set();
        const docTypes = new Set();
        const years = new Set();
        
        data.results.forEach(result => {
          if (result.court) courts.add(result.court);
          if (result.type) docTypes.add(result.type);
          if (result.date) {
            const year = new Date(result.date).getFullYear();
            if (!isNaN(year)) years.add(year);
          }
        });
        
        setFilters({
          courts: Array.from(courts).sort(),
          docTypes: Array.from(docTypes).sort(),
          years: Array.from(years).sort((a, b) => b - a) // Sort years descending
        });
        
        // Add to search history
        const historyItem = {
          id: Date.now(),
          query,
          jurisdiction,
          type: searchType,
          dateRange,
          timestamp: new Date().toISOString(),
          resultCount: data.results.length
        };
        
        setSearchHistory(prev => [historyItem, ...prev.slice(0, 9)]); // Keep last 10 searches
      } else {
        console.error('Search error:', data.error);
      }
    } catch (error) {
      console.error('Error performing search:', error);
    } finally {
      setIsSearching(false);
    }
  };

  // Handle filter changes
  const handleFilterChange = (filterType, value, isChecked) => {
    setAppliedFilters(prev => {
      const newFilters = { ...prev };
      
      if (isChecked) {
        newFilters[filterType] = [...prev[filterType], value];
      } else {
        newFilters[filterType] = prev[filterType].filter(item => item !== value);
      }
      
      return newFilters;
    });
  };

  // Clear all filters
  const clearFilters = () => {
    setAppliedFilters({
      courts: [],
      docTypes: [],
      years: []
    });
  };

  // Handle result selection
  const handleResultSelect = (result) => {
    setSelectedResult(result);
  };

  // Handle history item click
  const handleHistoryItemClick = (historyItem) => {
    setQuery(historyItem.query);
    setJurisdiction(historyItem.jurisdiction);
    setSearchType(historyItem.type);
    setDateRange(historyItem.dateRange);
    
    // Trigger search
    setTimeout(() => handleSearch(), 0);
  };

  // Format date
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    return isNaN(date) ? dateString : date.toLocaleDateString();
  };

  // Render filters section
  const renderFilters = () => {
    return (
      <div className="search-filters">
        <h3>Filters</h3>
        
        <div className="filter-actions">
          <button 
            className="clear-filters-button"
            onClick={clearFilters}
            disabled={!Object.values(appliedFilters).some(arr => arr.length > 0)}
          >
            Clear All Filters
          </button>
        </div>
        
        {filters.courts.length > 0 && (
          <div className="filter-section">
            <h4>Courts</h4>
            {filters.courts.map(court => (
              <label key={court} className="filter-checkbox">
                <input 
                  type="checkbox"
                  checked={appliedFilters.courts.includes(court)}
                  onChange={(e) => handleFilterChange('courts', court, e.target.checked)}
                />
                {court}
              </label>
            ))}
          </div>
        )}
        
        {filters.docTypes.length > 0 && (
          <div className="filter-section">
            <h4>Document Types</h4>
            {filters.docTypes.map(type => (
              <label key={type} className="filter-checkbox">
                <input 
                  type="checkbox"
                  checked={appliedFilters.docTypes.includes(type)}
                  onChange={(e) => handleFilterChange('docTypes', type, e.target.checked)}
                />
                {type}
              </label>
            ))}
          </div>
        )}
        
        {filters.years.length > 0 && (
          <div className="filter-section">
            <h4>Years</h4>
            {filters.years.map(year => (
              <label key={year} className="filter-checkbox">
                <input 
                  type="checkbox"
                  checked={appliedFilters.years.includes(year)}
                  onChange={(e) => handleFilterChange('years', year, e.target.checked)}
                />
                {year}
              </label>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="legal-search">
      <div className="search-header">
        <h2>Legal Research</h2>
      </div>
      
      <div className="search-container">
        <form onSubmit={handleSearch} className="search-form">
          <div className="search-input-container">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search legal cases, statutes, or commentary..."
              className="search-input"
              disabled={isSearching}
            />
            
            <button 
              type="submit" 
              className="search-button"
              disabled={isSearching || !query.trim()}
            >
              {isSearching ? (
                <div className="spinner small"></div>
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="11" cy="11" r="8"></circle>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                </svg>
              )}
            </button>
          </div>
          
          <div className="search-options">
            <div className="search-option">
              <label>Jurisdiction:</label>
              <select 
                value={jurisdiction}
                onChange={(e) => setJurisdiction(e.target.value)}
                disabled={isSearching}
              >
                <option value="US">United States</option>
                <option value="UK">United Kingdom</option>
                <option value="CA">Canada</option>
                <option value="AU">Australia</option>
                <option value="EU">European Union</option>
                <option value="INT">International</option>
              </select>
            </div>
            
            <div className="search-option">
              <label>Type:</label>
              <select 
                value={searchType}
                onChange={(e) => setSearchType(e.target.value)}
                disabled={isSearching}
              >
                <option value="all">All</option>
                <option value="case_law">Case Law</option>
                <option value="statute">Statutes</option>
                <option value="commentary">Commentary</option>
                <option value="article">Articles</option>
              </select>
            </div>
            
            <div className="search-option">
              <label>Date:</label>
              <select 
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value)}
                disabled={isSearching}
              >
                <option value="all">All Time</option>
                <option value="last_year">Last Year</option>
                <option value="last_5_years">Last 5 Years</option>
                <option value="last_10_years">Last 10 Years</option>
                <option value="custom">Custom Range</option>
              </select>
            </div>
          </div>
        </form>
        
        <div className="search-content">
          <div className="search-sidebar">
            {results.length > 0 && renderFilters()}
            
            {searchHistory.length > 0 && (
              <div className="search-history">
                <h3>Recent Searches</h3>
                <ul className="history-list">
                  {searchHistory.map(item => (
                    <li 
                      key={item.id}
                      className="history-item"
                      onClick={() => handleHistoryItemClick(item)}
                    >
                      <div className="history-query">{item.query}</div>
                      <div className="history-meta">
                        <span>{item.jurisdiction}</span>
                        <span>•</span>
                        <span>{item.resultCount} results</span>
                      </div>
                      <div className="history-time">
                        {new Date(item.timestamp).toLocaleDateString()}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
          
          <div className="search-results-container">
            {isSearching ? (
              <div className="loading-container">
                <div className="spinner"></div>
                <p>Searching legal resources...</p>
              </div>
            ) : results.length > 0 ? (
              <div className="search-results">
                <h3>Results ({results.length})</h3>
                
                <ul className="results-list">
                  {results.map((result, index) => (
                    <li 
                      key={index}
                      className={`result-item ${selectedResult === result ? 'selected' : ''}`}
                      onClick={() => handleResultSelect(result)}
                    >
                      <div className="result-title">{result.title}</div>
                      
                      <div className="result-meta">
                        {result.court && <span className="result-court">{result.court}</span>}
                        {result.citation && <span className="result-citation">{result.citation}</span>}
                        {result.date && <span className="result-date">{formatDate(result.date)}</span>}
                        {result.type && <span className="result-type">{result.type}</span>}
                      </div>
                      
                      {result.summary && (
                        <div className="result-summary">{result.summary}</div>
                      )}
                      
                      {result.url && (
                        <a 
                          href={result.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="result-link"
                          onClick={(e) => e.stopPropagation()}
                        >
                          View Source
                        </a>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            ) : query ? (
              <div className="no-results">
                <p>No results found for "{query}".</p>
                <p>Try adjusting your search terms or filters.</p>
              </div>
            ) : (
              <div className="search-placeholder">
                <div className="placeholder-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="11" cy="11" r="8"></circle>
                    <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                  </svg>
                </div>
                <h3>Search Legal Resources</h3>
                <p>Enter a query to search for case law, statutes, and legal commentary.</p>
              </div>
            )}
          </div>
          
          {selectedResult && (
            <div className="result-details">
              <h3>Document Details</h3>
              
              <div className="detail-header">
                <h4>{selectedResult.title}</h4>
                
                <div className="detail-actions">
                  {selectedResult.url && (
                    <a 
                      href={selectedResult.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="detail-action-button"
                    >
                      Open Source
                    </a>
                  )}
                  
                  <button 
                    className="detail-action-button"
                    onClick={() => {
                      // Save to session
                      fetch('/api/session/save-document', {
                        method: 'POST',
                        headers: {
                          'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                          document: selectedResult
                        })
                      });
                    }}
                  >
                    Save to Session
                  </button>
                </div>
              </div>
              
              <div className="detail-meta">
                {selectedResult.court && (
                  <div className="detail-item">
                    <strong>Court:</strong> {selectedResult.court}
                  </div>
                )}
                
                {selectedResult.citation && (
                  <div className="detail-item">
                    <strong>Citation:</strong> {selectedResult.citation}
                  </div>
                )}
                
                {selectedResult.date && (
                  <div className="detail-item">
                    <strong>Date:</strong> {formatDate(selectedResult.date)}
                  </div>
                )}
                
                {selectedResult.type && (
                  <div className="detail-item">
                    <strong>Type:</strong> {selectedResult.type}
                  </div>
                )}
              </div>
              
              {selectedResult.summary && (
                <div className="detail-section">
                  <h5>Summary</h5>
                  <div className="detail-content">{selectedResult.summary}</div>
                </div>
              )}
              
              {selectedResult.content && (
                <div className="detail-section">
                  <h5>Content</h5>
                  <div className="detail-content">{selectedResult.content}</div>
                </div>
              )}
              
              {selectedResult.key_points && selectedResult.key_points.length > 0 && (
                <div className="detail-section">
                  <h5>Key Points</h5>
                  <ul className="detail-list">
                    {selectedResult.key_points.map((point, index) => (
                      <li key={index}>{point}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LegalSearch;
