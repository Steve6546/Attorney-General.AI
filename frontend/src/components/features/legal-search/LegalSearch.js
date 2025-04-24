"""
Attorney-General.AI - Legal Search Component

This component implements the legal search interface for searching legal information.
"""

import React, { useState } from 'react';
import './LegalSearch.css';

const LegalSearch = () => {
  const [query, setQuery] = useState('');
  const [jurisdiction, setJurisdiction] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState(null);
  const [hasSearched, setHasSearched] = useState(false);

  // Handle search submission
  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    try {
      setLoading(true);
      setError(null);
      setHasSearched(true);
      
      // Call the legal research API
      const response = await fetch('/api/v1/legal_research', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          jurisdiction: jurisdiction || undefined,
          max_results: 10
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to perform legal search');
      }
      
      const data = await response.json();
      setResults(data.results || []);
      
    } catch (err) {
      setError(err.message);
      console.error('Error performing legal search:', err);
    } finally {
      setLoading(false);
    }
  };

  // Handle query input change
  const handleQueryChange = (e) => {
    setQuery(e.target.value);
  };

  // Handle jurisdiction selection
  const handleJurisdictionChange = (e) => {
    setJurisdiction(e.target.value);
  };

  return (
    <div className="legal-search">
      <div className="search-header">
        <h2>البحث القانوني</h2>
      </div>
      
      <div className="search-form-container">
        <form onSubmit={handleSearch} className="search-form">
          <div className="search-input-group">
            <input
              type="text"
              className="search-input"
              value={query}
              onChange={handleQueryChange}
              placeholder="ادخل استفسارك القانوني..."
              required
            />
            <select
              className="jurisdiction-select"
              value={jurisdiction}
              onChange={handleJurisdictionChange}
            >
              <option value="">كل الولايات القضائية</option>
              <option value="US">الولايات المتحدة</option>
              <option value="UK">المملكة المتحدة</option>
              <option value="EU">الاتحاد الأوروبي</option>
              <option value="CA">كندا</option>
              <option value="AU">أستراليا</option>
            </select>
            <button 
              type="submit" 
              className="search-button"
              disabled={loading || !query.trim()}
            >
              بحث
            </button>
          </div>
        </form>
      </div>
      
      <div className="search-results-container">
        {loading ? (
          <div className="loading-indicator">جاري البحث...</div>
        ) : error ? (
          <div className="error-message">
            {error}
          </div>
        ) : hasSearched && results.length === 0 ? (
          <div className="empty-results">
            <p>لم يتم العثور على نتائج لاستفسارك.</p>
            <p>حاول استخدام كلمات مفتاحية مختلفة أو تغيير الولاية القضائية.</p>
          </div>
        ) : (
          <div className="results-list">
            {results.map((result, index) => (
              <div key={index} className="result-item">
                <h3 className="result-title">{result.title}</h3>
                <div className="result-meta">
                  <span className="result-source">{result.source}</span>
                  <span className="result-relevance">
                    الصلة: {Math.round(result.relevance * 100)}%
                  </span>
                </div>
                <p className="result-summary">{result.summary}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default LegalSearch;
