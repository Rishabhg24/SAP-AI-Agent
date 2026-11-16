import React, { useState } from 'react';
import {
  CheckCircle2,
  AlertCircle,
  Copy,
  Download,
  RotateCcw,
  Search,
  ShieldCheck,
} from 'lucide-react';
import type { BulkCreationSummary, MasterDataType } from '../types';

interface Props {
  summary: BulkCreationSummary;
  masterType: MasterDataType;
  onReset: () => void;
}

export const BulkResultsViewer: React.FC<Props> = ({ summary, masterType, onReset }) => {
  const [filter, setFilter] = useState<'ALL' | 'CREATED' | 'DUPLICATE' | 'FAILED'>('ALL');
  const [search, setSearch] = useState('');

  const records = summary.records || [];

  const filteredRecords = records.filter((r) => {
    // Status filter
    if (filter === 'CREATED' && r.status !== 'CREATED') return false;
    if (filter === 'DUPLICATE' && r.status !== 'DUPLICATE') return false;
    if (filter === 'FAILED' && !['VALIDATION_ERROR', 'SAP_ERROR'].includes(r.status)) return false;

    // Search filter
    if (search) {
      const q = search.toLowerCase();
      const codeMatch = r.code?.toLowerCase().includes(q);
      const nameMatch = r.name?.toLowerCase().includes(q);
      const sapMatch = r.sap_object_id?.toLowerCase().includes(q);
      return codeMatch || nameMatch || sapMatch;
    }
    return true;
  });

  const exportCsv = () => {
    const headers = ['Record Index', 'Code', 'Name', 'Status', 'SAP Object ID', 'Duration (ms)', 'Error Details'];
    const rows = records.map((r) => [
      r.index + 1,
      `"${(r.code || '').replace(/"/g, '""')}"`,
      `"${(r.name || '').replace(/"/g, '""')}"`,
      r.status,
      `"${(r.sap_object_id || '').replace(/"/g, '""')}"`,
      r.duration_ms || '',
      `"${(r.error || '').replace(/"/g, '""')}"`,
    ]);

    const csvContent = [headers.join(','), ...rows.map((row) => row.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `sap_bulk_creation_${masterType}_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'CREATED':
        return (
          <span
            style={{
              padding: '3px 8px',
              borderRadius: 12,
              background: '#DCFCE7',
              border: '1px solid #BBF7D0',
              color: '#166534',
              fontSize: 11,
              fontWeight: 600,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 4,
            }}
          >
            <CheckCircle2 size={12} /> CREATED
          </span>
        );
      case 'DUPLICATE':
        return (
          <span
            style={{
              padding: '3px 8px',
              borderRadius: 12,
              background: '#FEF3C7',
              border: '1px solid #FDE68A',
              color: '#92400E',
              fontSize: 11,
              fontWeight: 600,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 4,
            }}
          >
            <Copy size={12} /> DUPLICATE (SKIPPED)
          </span>
        );
      default:
        return (
          <span
            style={{
              padding: '3px 8px',
              borderRadius: 12,
              background: '#FEE2E2',
              border: '1px solid #FECACA',
              color: '#991B1B',
              fontSize: 11,
              fontWeight: 600,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 4,
            }}
          >
            <AlertCircle size={12} /> {status}
          </span>
        );
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Top Banner */}
      <div
        className="glass-panel"
        style={{
          padding: 28,
          background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(15, 23, 42, 0.85) 100%)',
          border: '1px solid rgba(16, 185, 129, 0.35)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 20,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: '50%',
              background: 'rgba(16, 185, 129, 0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#34D399',
              boxShadow: '0 0 20px rgba(16, 185, 129, 0.3)',
            }}
          >
            <ShieldCheck size={32} />
          </div>
          <div>
            <h3 style={{ fontSize: 20, fontWeight: 700, color: '#34D399', marginBottom: 4 }}>
              Bulk Creation Completed in SAP!
            </h3>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
              Authoritative batch operation executed via Service Layer. All transactions immutably logged.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 12 }}>
          <button
            type="button"
            onClick={exportCsv}
            className="btn btn-secondary"
            style={{ fontSize: 13, padding: '10px 18px', display: 'flex', alignItems: 'center', gap: 8 }}
          >
            <Download size={15} /> Export Audit Log (CSV)
          </button>
          <button
            type="button"
            onClick={onReset}
            className="btn btn-primary"
            style={{ fontSize: 13, padding: '10px 18px', display: 'flex', alignItems: 'center', gap: 8 }}
          >
            <RotateCcw size={15} /> Process Another File
          </button>
        </div>
      </div>

      {/* 4 Metric Cards */}
      <div className="grid-4" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
        <div className="glass-panel" style={{ padding: 20 }}>
          <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            Total Submitted
          </span>
          <div style={{ fontSize: 28, fontWeight: 700, color: '#F8FAFC', marginTop: 4 }}>
            {summary.total_submitted}
          </div>
          <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Batch Records Processed</span>
        </div>

        <div className="glass-panel" style={{ padding: 20, borderLeft: '3px solid #10B981' }}>
          <span style={{ fontSize: 11, fontWeight: 600, color: '#34D399', textTransform: 'uppercase' }}>
            Created in SAP
          </span>
          <div style={{ fontSize: 28, fontWeight: 700, color: '#34D399', marginTop: 4 }}>
            {summary.created_count}
          </div>
          <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Service Layer HTTP 201</span>
        </div>

        <div className="glass-panel" style={{ padding: 20, borderLeft: '3px solid #F59E0B' }}>
          <span style={{ fontSize: 11, fontWeight: 600, color: '#FBBF24', textTransform: 'uppercase' }}>
            Duplicates Skipped
          </span>
          <div style={{ fontSize: 28, fontWeight: 700, color: '#FBBF24', marginTop: 4 }}>
            {summary.duplicate_count}
          </div>
          <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Pre-existing in SAP </span>
        </div>

        <div className="glass-panel" style={{ padding: 20, borderLeft: '3px solid #EF4444' }}>
          <span style={{ fontSize: 11, fontWeight: 600, color: '#F87171', textTransform: 'uppercase' }}>
            Failed / Errors
          </span>
          <div style={{ fontSize: 28, fontWeight: 700, color: summary.failed_count > 0 ? '#F87171' : 'var(--text-muted)', marginTop: 4 }}>
            {summary.failed_count}
          </div>
          <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Validation or SAP Errors</span>
        </div>
      </div>

      {/* Results Table Section */}
      <div className="glass-panel" style={{ padding: 24, display: 'flex', flexDirection: 'column', gap: 16 }}>
        {/* Table Controls */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <div style={{ display: 'flex', gap: 6, background: '#F1F5F9', padding: 4, borderRadius: 'var(--radius-md)', border: '1px solid #E2E8F0' }}>
            <button
              type="button"
              onClick={() => setFilter('ALL')}
              className={`btn ${filter === 'ALL' ? 'btn-primary' : 'btn-secondary'}`}
              style={{ padding: '6px 14px', fontSize: 12 }}
            >
              All ({records.length})
            </button>
            <button
              type="button"
              onClick={() => setFilter('CREATED')}
              className={`btn ${filter === 'CREATED' ? 'btn-primary' : 'btn-secondary'}`}
              style={{ padding: '6px 14px', fontSize: 12 }}
            >
              Created ({summary.created_count})
            </button>
            <button
              type="button"
              onClick={() => setFilter('DUPLICATE')}
              className={`btn ${filter === 'DUPLICATE' ? 'btn-primary' : 'btn-secondary'}`}
              style={{ padding: '6px 14px', fontSize: 12 }}
            >
              Duplicates ({summary.duplicate_count})
            </button>
            {summary.failed_count > 0 && (
              <button
                type="button"
                onClick={() => setFilter('FAILED')}
                className={`btn ${filter === 'FAILED' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ padding: '6px 14px', fontSize: 12, color: filter === 'FAILED' ? '#FFFFFF' : '#DC2626' }}
              >
                Failed ({summary.failed_count})
              </button>
            )}
          </div>

          <div style={{ position: 'relative', minWidth: 240 }}>
            <Search size={14} color="#64748B" style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)' }} />
            <input
              type="text"
              className="form-input"
              placeholder="Search by Code, Name, or SAP ID..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ paddingLeft: 30, fontSize: 12, height: 34 }}
            />
          </div>
        </div>

        {/* Records Table */}
        <div
          style={{
            background: '#FFFFFF',
            borderRadius: 'var(--radius-md)',
            border: '1px solid #E2E8F0',
            overflowX: 'auto',
            maxHeight: 450,
          }}
        >
          <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
            <thead>
              <tr>
                <th style={{ width: 50 }}>#</th>
                <th style={{ width: 140 }}>Code</th>
                <th>Name / Description</th>
                <th style={{ width: 150 }}>Status</th>
                <th style={{ width: 140 }}>SAP Object ID</th>
                <th style={{ width: 90 }}>Duration</th>
                <th>Details / Error</th>
              </tr>
            </thead>
            <tbody>
              {filteredRecords.map((rec) => (
                <tr key={rec.index}>
                  <td style={{ fontWeight: 600, color: '#64748B' }}>{rec.index + 1}</td>
                  <td style={{ fontWeight: 600, color: '#2563EB' }}>{rec.code}</td>
                  <td style={{ color: '#0F172A', fontWeight: 500 }}>{rec.name || '—'}</td>
                  <td>{getStatusBadge(rec.status)}</td>
                  <td>
                    {rec.sap_object_id ? (
                      <span style={{ fontFamily: 'monospace', fontWeight: 700, color: '#166534', background: '#DCFCE7', padding: '2px 6px', borderRadius: 4, border: '1px solid #BBF7D0' }}>
                        {rec.sap_object_id}
                      </span>
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>—</span>
                    )}
                  </td>
                  <td style={{ color: 'var(--text-muted)', fontSize: 11 }}>
                    {rec.duration_ms ? `${rec.duration_ms}ms` : '—'}
                  </td>
                  <td style={{ color: rec.error ? '#FCA5A5' : 'var(--text-muted)', fontSize: 11, maxWidth: 300, wordBreak: 'break-word' }}>
                    {rec.error || (rec.status === 'CREATED' ? 'Authoritative SAP Service Layer write confirmed' : '—')}
                  </td>
                </tr>
              ))}
              {filteredRecords.length === 0 && (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: 28, color: 'var(--text-muted)' }}>
                    No records match the current filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
