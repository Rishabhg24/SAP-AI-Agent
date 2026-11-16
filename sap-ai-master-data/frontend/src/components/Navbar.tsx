import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import type { SapHealthResponse } from '../types';
import { Database, ShieldCheck, Sparkles, RefreshCw, ChevronDown, Check, UserCheck } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, activeCompanyDb, activeCompanyName, availableCompanies, switchCompany, refreshCompanies } = useAuth();
  const [sapHealth, setSapHealth] = useState<SapHealthResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [isDbDropdownOpen, setIsDbDropdownOpen] = useState(false);
  const [isSwitchingDb, setIsSwitchingDb] = useState(false);

  const fetchHealth = async () => {
    setLoading(true);
    try {
      const data = await api.getSapHealth();
      setSapHealth(data);
      await refreshCompanies();
    } catch (e) {
      console.error('Failed to fetch SAP status', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleSelectCompany = async (companyDb: string) => {
    if (companyDb === activeCompanyDb) {
      setIsDbDropdownOpen(false);
      return;
    }
    setIsSwitchingDb(true);
    try {
      const ok = await switchCompany(companyDb);
      if (ok) {
        await fetchHealth();
      }
    } finally {
      setIsSwitchingDb(false);
      setIsDbDropdownOpen(false);
    }
  };

  return (
    <header className="navbar" style={{ position: 'relative', zIndex: 50 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <div style={{
          width: 38,
          height: 38,
          borderRadius: 8,
          background: 'linear-gradient(135deg, #0A85EA 0%, #034EA2 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 2px 10px rgba(10, 133, 234, 0.4)'
        }}>
          <Database size={20} color="#FFFFFF" />
        </div>
        <div>
          <h1 style={{ fontSize: 16, fontWeight: 700, letterSpacing: -0.3, margin: 0 }}>
            SAP AI Master Data <span style={{ color: '#0A85EA' }}>Platform</span>
          </h1>
          <p style={{ fontSize: 11, color: 'var(--text-secondary)', margin: 0 }}>
            Automated Creation via SAP Service Layer
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        {/* Company / Database Selector Dropdown */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => setIsDbDropdownOpen(!isDbDropdownOpen)}
            className="btn btn-secondary"
            style={{
              padding: '6px 12px',
              fontSize: 12,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              background: 'rgba(15, 23, 42, 0.85)',
              border: '1px solid rgba(10, 133, 234, 0.35)',
              borderRadius: 'var(--radius-full)',
              color: '#FFFFFF'
            }}
            title="Select SAP Company Database"
          >
            <div style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: sapHealth?.connected ? '#10B981' : '#F59E0B'
            }} />
            <span style={{ color: 'var(--text-secondary)' }}>Company:</span>
            <strong style={{ color: '#60A5FA', maxWidth: 190, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {activeCompanyName || activeCompanyDb}
            </strong>
            <span style={{
              fontSize: 10,
              padding: '1px 6px',
              borderRadius: 4,
              background: 'rgba(10, 133, 234, 0.2)',
              color: '#93C5FD',
              fontFamily: 'monospace'
            }}>
              {activeCompanyDb}
            </span>
            <ChevronDown size={14} color="#94A3B8" />
          </button>

          {/* Dropdown Menu */}
          {isDbDropdownOpen && (
            <div style={{
              position: 'absolute',
              top: 'calc(100% + 6px)',
              right: 0,
              width: 330,
              background: '#0F172A',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.6), 0 8px 10px -6px rgba(0, 0, 0, 0.6)',
              padding: 6,
              zIndex: 100
            }}>
              <div style={{ padding: '6px 10px', borderBottom: '1px solid rgba(255,255,255,0.08)', marginBottom: 4 }}>
                <span style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', color: '#94A3B8', letterSpacing: 0.5 }}>
                  Select SAP Database
                </span>
              </div>
              <div style={{ maxHeight: 280, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 2 }}>
                {availableCompanies.map((comp) => {
                  const isCurrent = comp.company_db.toUpperCase() === activeCompanyDb.toUpperCase();
                  return (
                    <button
                      key={comp.company_db}
                      disabled={isSwitchingDb}
                      onClick={() => handleSelectCompany(comp.company_db)}
                      style={{
                        padding: '8px 10px',
                        borderRadius: 6,
                        border: 'none',
                        background: isCurrent ? 'rgba(10, 133, 234, 0.15)' : 'transparent',
                        textAlign: 'left',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'flex-start',
                        justifyContent: 'space-between',
                        gap: 8,
                        transition: 'background 0.15s ease'
                      }}
                      onMouseEnter={(e) => {
                        if (!isCurrent) e.currentTarget.style.background = 'rgba(255,255,255,0.05)';
                      }}
                      onMouseLeave={(e) => {
                        if (!isCurrent) e.currentTarget.style.background = 'transparent';
                      }}
                    >
                      <div style={{ minWidth: 0 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <span style={{ fontSize: 12, fontWeight: 600, color: isCurrent ? '#60A5FA' : '#F1F5F9' }}>
                            {comp.company_name}
                          </span>
                          <span style={{
                            fontSize: 9.5,
                            padding: '1px 5px',
                            borderRadius: 3,
                            background: 'rgba(255,255,255,0.08)',
                            color: '#94A3B8'
                          }}>
                            {comp.localization}
                          </span>
                        </div>
                        <div style={{ fontSize: 11, color: '#94A3B8', fontFamily: 'monospace', marginTop: 1 }}>
                          DB: {comp.company_db}
                        </div>
                        {comp.description && (
                          <div style={{ fontSize: 10, color: '#64748B', marginTop: 2 }}>
                            {comp.description}
                          </div>
                        )}
                      </div>
                      {isCurrent && <Check size={16} color="#38BDF8" style={{ flexShrink: 0, marginTop: 2 }} />}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* User Badge */}
        {user && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 7,
            background: 'rgba(15, 23, 42, 0.7)',
            padding: '5px 12px',
            borderRadius: 'var(--radius-full)',
            border: '1px solid var(--border-subtle)',
            fontSize: 12
          }}>
            <UserCheck size={14} color="#38BDF8" />
            <span style={{ color: 'var(--text-secondary)' }}>User:</span>
            <strong style={{ color: '#F1F5F9', maxWidth: 130, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={user.email}>
              {user.name || user.email.split('@')[0]}
            </strong>
          </div>
        )}

        {/* SAP Status Pill */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          background: 'rgba(15, 23, 42, 0.7)',
          padding: '6px 12px',
          borderRadius: 'var(--radius-full)',
          border: '1px solid var(--border-subtle)',
          fontSize: 12
        }}>
          <ShieldCheck size={16} color={sapHealth?.connected ? '#10B981' : '#EF4444'} />
          <span style={{ color: 'var(--text-secondary)' }}>Status:</span>
          <strong style={{ color: sapHealth?.connected ? '#34D399' : '#F87171' }}>
            {sapHealth?.connected ? 'Live Connected' : 'Simulated'}
          </strong>
        </div>

        {/* NVIDIA Indicator */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          background: 'rgba(15, 23, 42, 0.7)',
          padding: '6px 12px',
          borderRadius: 'var(--radius-full)',
          border: '1px solid var(--border-subtle)',
          fontSize: 12
        }}>
          <Sparkles size={14} color="#8B5CF6" />
          <span style={{ color: 'var(--text-secondary)' }}>Nemotron AI</span>
        </div>

        {/* Refresh button */}
        <button
          onClick={fetchHealth}
          className="btn btn-secondary"
          style={{ padding: '6px 10px', fontSize: 12 }}
          title="Refresh connectivity status"
        >
          <RefreshCw size={14} className={loading || isSwitchingDb ? 'pulse-animation' : ''} />
        </button>
      </div>
    </header>
  );
};

