import React, { useState } from 'react';
import { api } from '../services/api';
import type { RAGSearchResult } from '../types';
import { Search, BookOpen, Sparkles, Send, FileText, CheckCircle2 } from 'lucide-react';

export const RagExplorer: React.FC = () => {
  const [activeMode, setActiveMode] = useState<'ask' | 'search'>('ask');
  const [query, setQuery] = useState('');
  const [entityFilter, setEntityFilter] = useState('all');
  const [loading, setLoading] = useState(false);
  const [searchResults, setSearchResults] = useState<RAGSearchResult[]>([]);
  const [askAnswer, setAskAnswer] = useState<{ answer: string; sources: any[] } | null>(null);

  const sampleQueries = [
    'What fields are required for creating a warehouse?',
    'What are the mandatory fields for Item Master in SAP?',
    'What CardType enum values are supported for Business Partners?',
    'How does the Service Layer handle session cookies and authentication?',
    'What are the CINNTRA_DEMO_NEW company rules for Business Partners?'
  ];

  const handleExecute = async (overrideQuery?: string) => {
    const q = overrideQuery || query;
    if (!q.trim() || loading) return;

    setLoading(true);
    setSearchResults([]);
    setAskAnswer(null);

    try {
      if (activeMode === 'search') {
        const results = await api.searchRag(q, 5, entityFilter !== 'all' ? entityFilter : undefined);
        setSearchResults(results);
      } else {
        const res = await api.askRag(q, entityFilter !== 'all' ? entityFilter : undefined);
        setAskAnswer(res);
      }
    } catch (e) {
      console.error('RAG request failed', e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Header */}
      <div>
        <h2 style={{ fontSize: 24, fontWeight: 700, letterSpacing: -0.4 }}>
          SAP Knowledge Base & RAG Retrieval
        </h2>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
          Search official SAP 10.0 Service Layer documentation and ask questions grounded in local vectors
        </p>
      </div>

      {/* Query Card */}
      <div className="glass-panel" style={{ padding: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <div style={{ display: 'flex', gap: 8 }}>
            <button
              onClick={() => setActiveMode('ask')}
              className={`btn ${activeMode === 'ask' ? 'btn-primary' : 'btn-secondary'}`}
              style={{ padding: '8px 16px', fontSize: 13 }}
            >
              <Sparkles size={15} /> Grounded AI Q&A
            </button>
            <button
              onClick={() => setActiveMode('search')}
              className={`btn ${activeMode === 'search' ? 'btn-primary' : 'btn-secondary'}`}
              style={{ padding: '8px 16px', fontSize: 13 }}
            >
              <Search size={15} /> Semantic Vector Search
            </button>
          </div>

          {/* Entity Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Entity Filter:</span>
            <select
              value={entityFilter}
              onChange={(e) => setEntityFilter(e.target.value)}
              className="form-select"
              style={{ padding: '6px 12px', fontSize: 13, width: 'auto' }}
            >
              <option value="all">All Categories</option>
              <option value="Item">Item Master</option>
              <option value="BusinessPartner">Business Partner</option>
              <option value="Warehouse">Warehouse</option>
              <option value="ServiceLayer">Service Layer</option>
              <option value="CompanyRules">Company Rules</option>
            </select>
          </div>
        </div>

        {/* Input Bar */}
        <div style={{ display: 'flex', gap: 10, marginBottom: 16 }}>
          <input
            type="text"
            className="form-input"
            placeholder={
              activeMode === 'ask'
                ? 'Ask any question regarding SAP Service Layer rules...'
                : 'Enter semantic search terms (e.g., warehouse required properties)...'
            }
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleExecute()}
            style={{ fontSize: 14, padding: '12px 16px' }}
          />
          <button
            onClick={() => handleExecute()}
            disabled={loading || !query.trim()}
            className="btn btn-primary"
            style={{ padding: '0 24px' }}
          >
            {loading ? 'Searching...' : <Send size={16} />}
          </button>
        </div>

        {/* Sample Queries */}
        <div>
          <span style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 8 }}>
            Sample Technical Queries:
          </span>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {sampleQueries.map((sq, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setQuery(sq);
                  handleExecute(sq);
                }}
                className="btn btn-secondary"
                style={{ padding: '5px 12px', fontSize: 12, borderRadius: 'var(--radius-full)' }}
              >
                {sq}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Answer Panel (Grounded Q&A) */}
      {askAnswer && (
        <div
          className="glass-panel"
          style={{
            padding: 24,
            borderLeft: '4px solid #2563EB',
            background: '#FFFFFF',
            border: '1px solid #E2E8F0',
            borderLeftWidth: 4,
            borderRadius: 14,
            boxShadow: '0 4px 16px rgba(15, 23, 42, 0.04)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
            <Sparkles size={18} color="#2563EB" />
            <h3 style={{ fontSize: 16, fontWeight: 700, color: '#0F172A' }}>Grounded Technical Answer</h3>
          </div>
          <div
            style={{
              fontSize: 14.5,
              lineHeight: 1.75,
              color: '#0F172A',
              whiteSpace: 'pre-wrap',
              marginBottom: 20
            }}
          >
            {askAnswer.answer}
          </div>

          {/* Citations */}
          {askAnswer.sources && askAnswer.sources.length > 0 && (
            <div
              style={{
                background: '#F8FAFC',
                padding: 16,
                borderRadius: 12,
                border: '1px solid #E2E8F0'
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  marginBottom: 10,
                  color: '#2563EB',
                  fontSize: 13,
                  fontWeight: 600
                }}
              >
                <BookOpen size={14} /> Authoritative SAP Documentation Citations:
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {askAnswer.sources.map((src, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      fontSize: 12.5,
                      color: '#475569'
                    }}
                  >
                    <CheckCircle2 size={14} color="#10B981" />
                    <strong style={{ color: '#0F172A', fontWeight: 600 }}>{src.document}</strong>
                    <span>•</span>
                    <span>Section: {src.section}</span>
                    {src.page && <span>(Page {src.page})</span>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Semantic Search Results */}
      {searchResults.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <h3 style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-secondary)' }}>
            Retrieved Chunks ({searchResults.length})
          </h3>
          {searchResults.map((res, idx) => (
            <div key={idx} className="glass-panel" style={{ padding: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <FileText size={16} color="#2563EB" />
                  <strong style={{ fontSize: 14, color: '#0F172A' }}>{res.source}</strong>
                  <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                    ({res.metadata?.section || 'General'})
                  </span>
                </div>
                <span className="badge badge-success" style={{ fontSize: 11 }}>
                  Score: {(res.score * 100).toFixed(1)}%
                </span>
              </div>
              <div style={{
                background: '#F8FAFC',
                border: '1px solid #E2E8F0',
                padding: 14,
                borderRadius: 'var(--radius-sm)',
                fontSize: 13,
                lineHeight: 1.6,
                color: '#1E293B',
                whiteSpace: 'pre-wrap'
              }}>
                {res.content}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
